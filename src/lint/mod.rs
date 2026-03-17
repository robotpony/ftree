use crate::model::FamilyTree;
use std::fmt;

/// Category of a lint warning.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LintCategory {
    /// A cross-reference points to a record that does not exist.
    DanglingReference,
    /// Dates within a record are logically inconsistent.
    DateInconsistency,
}

impl fmt::Display for LintCategory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LintCategory::DanglingReference => write!(f, "dangling-ref"),
            LintCategory::DateInconsistency => write!(f, "date"),
        }
    }
}

/// A data quality issue found after parsing.
#[derive(Debug, Clone)]
pub struct LintWarning {
    pub category: LintCategory,
    pub message: String,
}

impl fmt::Display for LintWarning {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}] {}", self.category, self.message)
    }
}

/// Run all lint rules against a parsed family tree.
/// Returns data quality issues found, sorted by category then message.
pub fn lint(tree: &FamilyTree) -> Vec<LintWarning> {
    let mut warnings = Vec::new();
    check_dangling_refs(tree, &mut warnings);
    check_date_inconsistencies(tree, &mut warnings);
    warnings.sort_by(|a, b| {
        a.category
            .to_string()
            .cmp(&b.category.to_string())
            .then(a.message.cmp(&b.message))
    });
    warnings
}

// ---------------------------------------------------------------------------
// Rule: Dangling cross-references
// ---------------------------------------------------------------------------

fn check_dangling_refs(tree: &FamilyTree, out: &mut Vec<LintWarning>) {
    // INDI.family_as_spouse → FAM must exist
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort();
    for xref in &xrefs {
        let indi = &tree.individuals[*xref];
        let name = indi.display_name();

        for fam_xref in &indi.family_as_spouse {
            if !tree.families.contains_key(fam_xref) {
                out.push(dangling(format!(
                    "{} ({}): FAMS references unknown family {}",
                    name, xref, fam_xref
                )));
            }
        }

        for fam_xref in &indi.family_as_child {
            if !tree.families.contains_key(fam_xref) {
                out.push(dangling(format!(
                    "{} ({}): FAMC references unknown family {}",
                    name, xref, fam_xref
                )));
            }
        }

        for citation in &indi.source_citations {
            if !tree.sources.contains_key(&citation.source_xref) {
                out.push(dangling(format!(
                    "{} ({}): SOUR citation references unknown source {}",
                    name, xref, citation.source_xref
                )));
            }
        }

        for media in &indi.media {
            if let Some(ref obj_xref) = media.xref {
                if !tree.multimedia_objects.contains_key(obj_xref) {
                    out.push(dangling(format!(
                        "{} ({}): OBJE pointer references unknown multimedia object {}",
                        name, xref, obj_xref
                    )));
                }
            }
        }
    }

    // FAM references → INDI must exist
    let mut fam_xrefs: Vec<&String> = tree.families.keys().collect();
    fam_xrefs.sort();
    for fam_xref in &fam_xrefs {
        let fam = &tree.families[*fam_xref];

        if let Some(ref husb) = fam.husband {
            if !tree.individuals.contains_key(husb) {
                out.push(dangling(format!(
                    "Family {}: HUSB references unknown individual {}",
                    fam_xref, husb
                )));
            }
        }
        if let Some(ref wife) = fam.wife {
            if !tree.individuals.contains_key(wife) {
                out.push(dangling(format!(
                    "Family {}: WIFE references unknown individual {}",
                    fam_xref, wife
                )));
            }
        }
        for child in &fam.children {
            if !tree.individuals.contains_key(child) {
                out.push(dangling(format!(
                    "Family {}: CHIL references unknown individual {}",
                    fam_xref, child
                )));
            }
        }
    }

    // SOUR.repository_xref → REPO must exist
    let mut sour_xrefs: Vec<&String> = tree.sources.keys().collect();
    sour_xrefs.sort();
    for sour_xref in &sour_xrefs {
        let source = &tree.sources[*sour_xref];
        if let Some(ref repo_xref) = source.repository_xref {
            if !tree.repositories.contains_key(repo_xref) {
                out.push(dangling(format!(
                    "Source {}: REPO pointer references unknown repository {}",
                    sour_xref, repo_xref
                )));
            }
        }
    }
}

fn dangling(message: String) -> LintWarning {
    LintWarning {
        category: LintCategory::DanglingReference,
        message,
    }
}

fn date_issue(message: String) -> LintWarning {
    LintWarning {
        category: LintCategory::DateInconsistency,
        message,
    }
}

// ---------------------------------------------------------------------------
// Rule: Date inconsistencies
// ---------------------------------------------------------------------------

fn check_date_inconsistencies(tree: &FamilyTree, out: &mut Vec<LintWarning>) {
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort();

    for xref in &xrefs {
        let indi = &tree.individuals[*xref];
        let name = indi.display_name();

        let birth_year = indi.birth.as_ref().and_then(|e| e.date.as_ref()).and_then(|d| d.year);
        let death_year = indi.death.as_ref().and_then(|e| e.date.as_ref()).and_then(|d| d.year);

        // Death before birth
        if let (Some(b), Some(d)) = (birth_year, death_year) {
            if d < b {
                out.push(date_issue(format!(
                    "{} ({}): death year {} precedes birth year {}",
                    name, xref, d, b
                )));
            }
        }
    }

    // Marriage before birth of spouse
    let mut fam_xrefs: Vec<&String> = tree.families.keys().collect();
    fam_xrefs.sort();

    for fam_xref in &fam_xrefs {
        let fam = &tree.families[*fam_xref];

        let marriage_year = fam
            .marriage
            .as_ref()
            .and_then(|e| e.date.as_ref())
            .and_then(|d| d.year);

        if let Some(marr_year) = marriage_year {
            for (role, indi_xref_opt) in [("husband", &fam.husband), ("wife", &fam.wife)] {
                if let Some(indi_xref) = indi_xref_opt {
                    if let Some(indi) = tree.individuals.get(indi_xref) {
                        let birth_year = indi
                            .birth
                            .as_ref()
                            .and_then(|e| e.date.as_ref())
                            .and_then(|d| d.year);
                        if let Some(b) = birth_year {
                            if marr_year < b {
                                out.push(date_issue(format!(
                                    "Family {}: marriage year {} precedes {} {} birth year {}",
                                    fam_xref,
                                    marr_year,
                                    role,
                                    indi.display_name(),
                                    b
                                )));
                            }
                        }
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::*;

    fn clean_tree() -> FamilyTree {
        let mut tree = FamilyTree::new();

        let mut john = Individual::new("@I1@".to_string());
        john.name = Some(Name::from_gedcom("John /Smith/"));
        john.sex = Some(Sex::Male);
        john.birth = Some(Event {
            date: Some(Date::parse("1900")),
            place: None,
        });
        john.death = Some(Event {
            date: Some(Date::parse("1980")),
            place: None,
        });
        john.family_as_spouse.push("@F1@".to_string());

        let mut jane = Individual::new("@I2@".to_string());
        jane.name = Some(Name::from_gedcom("Jane /Doe/"));
        jane.sex = Some(Sex::Female);
        jane.birth = Some(Event {
            date: Some(Date::parse("1905")),
            place: None,
        });
        jane.family_as_spouse.push("@F1@".to_string());

        let mut bob = Individual::new("@I3@".to_string());
        bob.name = Some(Name::from_gedcom("Bob /Smith/"));
        bob.family_as_child.push("@F1@".to_string());

        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.wife = Some("@I2@".to_string());
        fam.children.push("@I3@".to_string());
        fam.marriage = Some(Event {
            date: Some(Date::parse("1925")),
            place: None,
        });

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    #[test]
    fn test_clean_tree_no_warnings() {
        let tree = clean_tree();
        let warnings = lint(&tree);
        assert!(
            warnings.is_empty(),
            "Clean tree should produce no lint warnings, got: {:?}",
            warnings
        );
    }

    #[test]
    fn test_dangling_fams() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.family_as_spouse.push("@F99@".to_string()); // doesn't exist
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert_eq!(warnings[0].category, LintCategory::DanglingReference);
        assert!(warnings[0].message.contains("FAMS"));
        assert!(warnings[0].message.contains("@F99@"));
    }

    #[test]
    fn test_dangling_famc() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("Jane /Doe/"));
        indi.family_as_child.push("@F99@".to_string()); // doesn't exist
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("FAMC"));
        assert!(warnings[0].message.contains("@F99@"));
    }

    #[test]
    fn test_dangling_family_husb() {
        let mut tree = FamilyTree::new();
        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I99@".to_string()); // doesn't exist
        tree.families.insert("@F1@".to_string(), fam);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("HUSB"));
        assert!(warnings[0].message.contains("@I99@"));
    }

    #[test]
    fn test_dangling_family_wife() {
        let mut tree = FamilyTree::new();
        let mut fam = Family::new("@F1@".to_string());
        fam.wife = Some("@I99@".to_string()); // doesn't exist
        tree.families.insert("@F1@".to_string(), fam);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("WIFE"));
        assert!(warnings[0].message.contains("@I99@"));
    }

    #[test]
    fn test_dangling_family_chil() {
        let mut tree = FamilyTree::new();
        let mut fam = Family::new("@F1@".to_string());
        fam.children.push("@I99@".to_string()); // doesn't exist
        tree.families.insert("@F1@".to_string(), fam);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("CHIL"));
        assert!(warnings[0].message.contains("@I99@"));
    }

    #[test]
    fn test_dangling_source_citation() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.source_citations.push(SourceCitation {
            source_xref: "@S99@".to_string(),
            page: None,
            quality: None,
        });
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("SOUR"));
        assert!(warnings[0].message.contains("@S99@"));
    }

    #[test]
    fn test_dangling_obje_pointer() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.media.push(MediaRef {
            file: None,
            xref: Some("@O99@".to_string()),
        });
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("OBJE"));
        assert!(warnings[0].message.contains("@O99@"));
    }

    #[test]
    fn test_dangling_source_repo() {
        let mut tree = FamilyTree::new();
        let mut source = Source::new("@S1@".to_string());
        source.title = Some("My Source".to_string());
        source.repository_xref = Some("@R99@".to_string()); // doesn't exist
        tree.sources.insert("@S1@".to_string(), source);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].message.contains("REPO"));
        assert!(warnings[0].message.contains("@R99@"));
    }

    #[test]
    fn test_death_before_birth() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.birth = Some(Event {
            date: Some(Date::parse("1900")),
            place: None,
        });
        indi.death = Some(Event {
            date: Some(Date::parse("1850")), // before birth
            place: None,
        });
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 1);
        assert_eq!(warnings[0].category, LintCategory::DateInconsistency);
        assert!(warnings[0].message.contains("death year 1850"));
        assert!(warnings[0].message.contains("birth year 1900"));
    }

    #[test]
    fn test_same_birth_death_year_ok() {
        // Same year is allowed (e.g. stillbirth or infant death)
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.birth = Some(Event { date: Some(Date::parse("1900")), place: None });
        indi.death = Some(Event { date: Some(Date::parse("1900")), place: None });
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert!(warnings.is_empty());
    }

    #[test]
    fn test_marriage_before_birth() {
        let mut tree = FamilyTree::new();

        let mut husb = Individual::new("@I1@".to_string());
        husb.name = Some(Name::from_gedcom("John /Smith/"));
        husb.birth = Some(Event {
            date: Some(Date::parse("1920")),
            place: None,
        });
        husb.family_as_spouse.push("@F1@".to_string());
        tree.individuals.insert("@I1@".to_string(), husb);

        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.marriage = Some(Event {
            date: Some(Date::parse("1910")), // before husband's birth
            place: None,
        });
        tree.families.insert("@F1@".to_string(), fam);

        let warnings = lint(&tree);
        // Should have: dangling (FAMS from INDI has no matching family? No — family exists)
        // Actually: one date inconsistency (marriage before husband's birth)
        let date_warnings: Vec<_> = warnings
            .iter()
            .filter(|w| w.category == LintCategory::DateInconsistency)
            .collect();
        assert_eq!(date_warnings.len(), 1);
        assert!(date_warnings[0].message.contains("marriage year 1910"));
        assert!(date_warnings[0].message.contains("birth year 1920"));
    }

    #[test]
    fn test_multiple_issues_reported() {
        let mut tree = FamilyTree::new();

        // Individual with death before birth AND dangling FAMS
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("Ghost /Person/"));
        indi.birth = Some(Event { date: Some(Date::parse("1950")), place: None });
        indi.death = Some(Event { date: Some(Date::parse("1900")), place: None });
        indi.family_as_spouse.push("@F99@".to_string());
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert_eq!(warnings.len(), 2);

        let categories: Vec<_> = warnings.iter().map(|w| &w.category).collect();
        assert!(categories.contains(&&LintCategory::DanglingReference));
        assert!(categories.contains(&&LintCategory::DateInconsistency));
    }

    #[test]
    fn test_missing_birth_or_death_year_skips_date_check() {
        // If only one of birth/death has a parseable year, no date inconsistency
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("John /Smith/"));
        indi.birth = Some(Event {
            date: Some(Date::parse("ABT 1900")), // year parseable
            place: None,
        });
        indi.death = Some(Event {
            date: Some(Date::parse("(sometime in the past)")), // phrase, no year
            place: None,
        });
        tree.individuals.insert("@I1@".to_string(), indi);

        let warnings = lint(&tree);
        assert!(warnings.is_empty());
    }
}
