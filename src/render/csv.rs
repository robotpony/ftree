use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

use crate::model::{FamilyTree, Individual, Sex};
use crate::render::{RenderError, Renderer};

/// Renders the family tree as a single CSV file with one row per individual.
pub struct CsvRenderer;

const HEADERS: &[&str] = &[
    "xref",
    "name",
    "given",
    "surname",
    "sex",
    "birth_date",
    "birth_place",
    "death_date",
    "death_place",
    "burial_date",
    "burial_place",
    "occupation",
    "father",
    "mother",
    "spouses",
    "sources",
];

impl Renderer for CsvRenderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError> {
        let content = render_csv(tree);
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(output, content)?;
        Ok(())
    }
}

/// Render the full CSV content for a family tree.
pub fn render_csv(tree: &FamilyTree) -> String {
    let mut out = String::new();

    // Header row
    out.push_str(&HEADERS.join(","));
    out.push('\n');

    // Sort by xref for deterministic output
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort();

    for xref in xrefs {
        let indi = &tree.individuals[xref];
        render_row(&mut out, indi, tree);
    }

    out
}

fn render_row(out: &mut String, indi: &Individual, tree: &FamilyTree) {
    let name = indi.name.as_ref();

    let fields: Vec<String> = vec![
        csv_escape(&indi.xref),
        csv_escape(indi.display_name()),
        csv_escape(name.and_then(|n| n.given.as_deref()).unwrap_or("")),
        csv_escape(name.and_then(|n| n.surname.as_deref()).unwrap_or("")),
        csv_escape(match &indi.sex {
            Some(Sex::Male) => "M",
            Some(Sex::Female) => "F",
            Some(Sex::Unknown) => "U",
            None => "",
        }),
        csv_escape(
            indi.birth
                .as_ref()
                .and_then(|e| e.date.as_ref())
                .map(|d| d.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(
            indi.birth
                .as_ref()
                .and_then(|e| e.place.as_ref())
                .map(|p| p.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(
            indi.death
                .as_ref()
                .and_then(|e| e.date.as_ref())
                .map(|d| d.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(
            indi.death
                .as_ref()
                .and_then(|e| e.place.as_ref())
                .map(|p| p.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(
            indi.burial
                .as_ref()
                .and_then(|e| e.date.as_ref())
                .map(|d| d.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(
            indi.burial
                .as_ref()
                .and_then(|e| e.place.as_ref())
                .map(|p| p.raw.as_str())
                .unwrap_or(""),
        ),
        csv_escape(indi.occupation.as_deref().unwrap_or("")),
        csv_escape(&resolve_parent_name(indi, tree, ParentRole::Father)),
        csv_escape(&resolve_parent_name(indi, tree, ParentRole::Mother)),
        csv_escape(&resolve_spouse_names(indi, tree)),
        csv_escape(&resolve_source_titles(indi, tree)),
    ];

    let _ = writeln!(out, "{}", fields.join(","));
}

enum ParentRole {
    Father,
    Mother,
}

fn resolve_parent_name(indi: &Individual, tree: &FamilyTree, role: ParentRole) -> String {
    for fam_xref in &indi.family_as_child {
        if let Some(fam) = tree.families.get(fam_xref) {
            let parent_xref = match role {
                ParentRole::Father => fam.husband.as_deref(),
                ParentRole::Mother => fam.wife.as_deref(),
            };
            if let Some(xref) = parent_xref {
                if let Some(parent) = tree.individuals.get(xref) {
                    return parent.display_name().to_string();
                }
            }
        }
    }
    String::new()
}

fn resolve_spouse_names(indi: &Individual, tree: &FamilyTree) -> String {
    let mut names = Vec::new();
    for fam_xref in &indi.family_as_spouse {
        if let Some(fam) = tree.families.get(fam_xref) {
            let spouse_xref = if fam.husband.as_deref() == Some(&indi.xref) {
                fam.wife.as_deref()
            } else {
                fam.husband.as_deref()
            };
            if let Some(xref) = spouse_xref {
                if let Some(spouse) = tree.individuals.get(xref) {
                    names.push(spouse.display_name().to_string());
                }
            }
        }
    }
    names.join("; ")
}

fn resolve_source_titles(indi: &Individual, tree: &FamilyTree) -> String {
    let mut titles = Vec::new();
    for citation in &indi.source_citations {
        let title = tree
            .sources
            .get(&citation.source_xref)
            .map(|s| s.display_title().to_string())
            .unwrap_or_else(|| citation.source_xref.clone());
        titles.push(title);
    }
    titles.join("; ")
}

/// Escape a value for CSV (RFC 4180).
/// Quotes the field if it contains commas, quotes, or newlines.
fn csv_escape(value: &str) -> String {
    if value.contains(',') || value.contains('"') || value.contains('\n') || value.contains('\r') {
        format!("\"{}\"", value.replace('"', "\"\""))
    } else {
        value.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::*;

    fn make_test_tree() -> FamilyTree {
        let mut tree = FamilyTree::new();

        let mut john = Individual::new("@I1@".to_string());
        john.name = Some(Name::from_gedcom("John /Smith/"));
        john.sex = Some(Sex::Male);
        john.birth = Some(Event {
            date: Some(Date::parse("1 Jan 1900")),
            place: Some(Place::new("Boston, MA, USA")),
        });
        john.death = Some(Event {
            date: Some(Date::parse("31 Dec 1980")),
            place: Some(Place::new("New York, NY, USA")),
        });
        john.family_as_spouse.push("@F1@".to_string());

        let mut jane = Individual::new("@I2@".to_string());
        jane.name = Some(Name::from_gedcom("Jane /Doe/"));
        jane.sex = Some(Sex::Female);
        jane.family_as_spouse.push("@F1@".to_string());

        let mut bob = Individual::new("@I3@".to_string());
        bob.name = Some(Name::from_gedcom("Robert /Smith/"));
        bob.sex = Some(Sex::Male);
        bob.family_as_child.push("@F1@".to_string());

        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.wife = Some("@I2@".to_string());
        fam.children.push("@I3@".to_string());
        fam.marriage = Some(Event {
            date: Some(Date::parse("25 Dec 1925")),
            place: Some(Place::new("Miami, FL, USA")),
        });

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    #[test]
    fn test_csv_escape_plain() {
        assert_eq!(csv_escape("hello"), "hello");
    }

    #[test]
    fn test_csv_escape_comma() {
        assert_eq!(csv_escape("Boston, MA"), "\"Boston, MA\"");
    }

    #[test]
    fn test_csv_escape_quotes() {
        assert_eq!(csv_escape("say \"hi\""), "\"say \"\"hi\"\"\"");
    }

    #[test]
    fn test_csv_escape_empty() {
        assert_eq!(csv_escape(""), "");
    }

    #[test]
    fn test_csv_header_row() {
        let tree = FamilyTree::new();
        let csv = render_csv(&tree);
        let first_line = csv.lines().next().unwrap();
        assert_eq!(
            first_line,
            "xref,name,given,surname,sex,birth_date,birth_place,death_date,death_place,burial_date,burial_place,occupation,father,mother,spouses,sources"
        );
    }

    #[test]
    fn test_csv_row_count() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        let lines: Vec<&str> = csv.lines().collect();
        // header + 3 individuals
        assert_eq!(lines.len(), 4);
    }

    #[test]
    fn test_csv_contains_names() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        assert!(csv.contains("John Smith"));
        assert!(csv.contains("Jane Doe"));
        assert!(csv.contains("Robert Smith"));
    }

    #[test]
    fn test_csv_places_are_quoted() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        // Places with commas should be quoted
        assert!(csv.contains("\"Boston, MA, USA\""));
        assert!(csv.contains("\"New York, NY, USA\""));
    }

    #[test]
    fn test_csv_parent_names() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        // Robert's row should contain his parents' names
        let robert_line = csv.lines().find(|l| l.starts_with("@I3@")).unwrap();
        assert!(robert_line.contains("John Smith"));
        assert!(robert_line.contains("Jane Doe"));
    }

    #[test]
    fn test_csv_spouse_names() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        // John's row should list Jane as spouse
        let john_line = csv.lines().find(|l| l.starts_with("@I1@")).unwrap();
        assert!(john_line.contains("Jane Doe"));
    }

    #[test]
    fn test_csv_sex_field() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        let john_line = csv.lines().find(|l| l.starts_with("@I1@")).unwrap();
        let fields: Vec<&str> = john_line.splitn(6, ',').collect();
        assert_eq!(fields[4], "M");
    }

    #[test]
    fn test_csv_source_titles() {
        let mut tree = make_test_tree();

        let mut source = Source::new("@S1@".to_string());
        source.title = Some("Birth Records".to_string());
        tree.sources.insert("@S1@".to_string(), source);

        tree.individuals
            .get_mut("@I1@")
            .unwrap()
            .source_citations
            .push(SourceCitation {
                source_xref: "@S1@".to_string(),
                page: Some("p. 42".to_string()),
                quality: None,
            });

        let csv = render_csv(&tree);
        let john_line = csv.lines().find(|l| l.starts_with("@I1@")).unwrap();
        assert!(john_line.contains("Birth Records"));
    }

    #[test]
    fn test_csv_empty_fields() {
        let tree = make_test_tree();
        let csv = render_csv(&tree);
        // Jane has no birth/death — fields should be empty
        let jane_line = csv.lines().find(|l| l.starts_with("@I2@")).unwrap();
        // After sex field (F), the next 4 fields (birth_date, birth_place, death_date, death_place) should be empty
        assert!(jane_line.contains(",F,,,,"));
    }
}
