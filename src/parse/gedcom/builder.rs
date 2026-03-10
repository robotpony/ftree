use crate::model::*;

use super::lexer::Token;

/// Build a FamilyTree from a sequence of GEDCOM tokens.
pub fn build(tokens: &[Token]) -> FamilyTree {
    let mut tree = FamilyTree::new();
    let mut i = 0;

    while i < tokens.len() {
        let token = &tokens[i];
        if token.level != 0 {
            i += 1;
            continue;
        }

        match token.tag.as_str() {
            "HEAD" => {
                let end = find_record_end(tokens, i);
                build_header(&mut tree, &tokens[i..end]);
                i = end;
            }
            "INDI" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let indi = build_individual(xref, &tokens[i..end], &mut tree.warnings);
                    tree.individuals.insert(xref.clone(), indi);
                }
                i = end;
            }
            "FAM" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let fam = build_family(xref, &tokens[i..end]);
                    tree.families.insert(xref.clone(), fam);
                }
                i = end;
            }
            "SUBM" | "TRLR" | "SUBN" => {
                i = find_record_end(tokens, i);
            }
            _ => {
                // Skip unrecognized level-0 records (SOUR, NOTE, REPO, etc.)
                let end = find_record_end(tokens, i);
                if !token.tag.starts_with('_') {
                    tree.warnings.push(ParseWarning {
                        line: Some(token.line_number),
                        message: format!("Skipping unhandled record type: {}", token.tag),
                    });
                }
                i = end;
            }
        }
    }

    tree
}

/// Find the index of the next level-0 token after position `start`.
fn find_record_end(tokens: &[Token], start: usize) -> usize {
    for i in (start + 1)..tokens.len() {
        if tokens[i].level == 0 {
            return i;
        }
    }
    tokens.len()
}

/// Find the first level-1 token with a given tag.
fn find_first<'a>(tokens: &'a [Token], level: u8, tag: &str) -> Option<&'a Token> {
    tokens
        .iter()
        .find(|t| t.level == level && t.tag == tag)
}

/// Get all subtokens belonging to a parent token (between parent and next same-or-lower level token).
fn get_children<'a>(tokens: &'a [Token], parent_idx: usize) -> &'a [Token] {
    let parent_level = tokens[parent_idx].level;
    let start = parent_idx + 1;
    for i in start..tokens.len() {
        if tokens[i].level <= parent_level {
            return &tokens[start..i];
        }
    }
    &tokens[start..]
}

fn build_header(tree: &mut FamilyTree, tokens: &[Token]) {
    // Find SOUR at level 1
    if let Some(sour) = find_first(tokens, 1, "SOUR") {
        tree.header.source = sour.value.clone();
    }

    // Find GEDC.VERS
    for (idx, token) in tokens.iter().enumerate() {
        if token.level == 1 && token.tag == "GEDC" {
            let children = get_children(tokens, idx);
            if let Some(vers) = find_first(children, 2, "VERS") {
                tree.header.gedcom_version = vers.value.clone();
            }
            if let Some(form) = find_first(children, 2, "FORM") {
                tree.header.gedcom_form = form.value.clone();
            }
            break;
        }
    }

    // Find CHAR
    if let Some(char_token) = find_first(tokens, 1, "CHAR") {
        tree.header.encoding = char_token.value.clone();
    }
}

fn build_individual(
    xref: &str,
    tokens: &[Token],
    warnings: &mut Vec<ParseWarning>,
) -> Individual {
    let mut indi = Individual::new(xref.to_string());

    for (idx, token) in tokens.iter().enumerate() {
        if token.level != 1 {
            continue;
        }

        match token.tag.as_str() {
            "NAME" => {
                if indi.name.is_none() {
                    let mut name = match &token.value {
                        Some(v) => Name::from_gedcom(v),
                        None => Name {
                            full: String::new(),
                            given: None,
                            surname: None,
                        },
                    };

                    // Override with explicit GIVN/SURN if present
                    let children = get_children(tokens, idx);
                    if let Some(givn) = find_first(children, 2, "GIVN") {
                        if let Some(ref v) = givn.value {
                            name.given = Some(v.clone());
                        }
                    }
                    if let Some(surn) = find_first(children, 2, "SURN") {
                        if let Some(ref v) = surn.value {
                            name.surname = Some(v.clone());
                        }
                    }

                    indi.name = Some(name);
                }
            }
            "SEX" => {
                if let Some(ref v) = token.value {
                    indi.sex = Some(match v.trim().to_uppercase().as_str() {
                        "M" => Sex::Male,
                        "F" => Sex::Female,
                        _ => Sex::Unknown,
                    });
                }
            }
            "BIRT" => {
                let children = get_children(tokens, idx);
                indi.birth = Some(build_event(children));
            }
            "DEAT" => {
                let children = get_children(tokens, idx);
                indi.death = Some(build_event(children));
            }
            "FAMS" => {
                if let Some(ref v) = token.value {
                    indi.family_as_spouse.push(v.clone());
                }
            }
            "FAMC" => {
                if let Some(ref v) = token.value {
                    indi.family_as_child.push(v.clone());
                }
            }
            "OBJE" => {
                let children = get_children(tokens, idx);
                let file = find_first(children, 2, "FILE")
                    .and_then(|t| t.value.clone());
                indi.media.push(MediaRef { file });
            }
            // Skip known but unhandled tags silently
            "CHAN" | "REFN" | "RIN" | "AFN" | "RFN" | "ALIA"
            | "EVEN" | "BURI" | "CHR" | "BAPM" | "ADOP"
            | "OCCU" | "RESI" | "EDUC" | "RELI" | "NATI"
            | "TITL" | "CAST" | "DSCR" | "IDNO" | "NCHI"
            | "NMR" | "PROP" | "SSN" | "FACT" | "NOTE" | "SOUR"
            | "CREM" | "CONF" | "GRAD" | "RETI" | "WILL"
            | "PROB" | "CENS" | "EMIG" | "IMMI" | "NATU"
            | "SUBM" | "ANCI" | "DESI" | "RESN" => {}
            tag if tag.starts_with('_') => {} // extension tags
            _ => {
                warnings.push(ParseWarning {
                    line: Some(token.line_number),
                    message: format!(
                        "Unknown tag in INDI {}: {}",
                        xref, token.tag
                    ),
                });
            }
        }
    }

    indi
}

fn build_family(xref: &str, tokens: &[Token]) -> Family {
    let mut fam = Family::new(xref.to_string());

    for (idx, token) in tokens.iter().enumerate() {
        if token.level != 1 {
            continue;
        }

        match token.tag.as_str() {
            "HUSB" => {
                fam.husband = token.value.clone();
            }
            "WIFE" => {
                fam.wife = token.value.clone();
            }
            "CHIL" => {
                if let Some(ref v) = token.value {
                    fam.children.push(v.clone());
                }
            }
            "MARR" => {
                let children = get_children(tokens, idx);
                fam.marriage = Some(build_event(children));
            }
            // Skip known but unhandled family tags
            "CHAN" | "REFN" | "RIN" | "NOTE" | "SOUR" | "OBJE"
            | "DIV" | "DIVF" | "ENGA" | "ANUL" | "EVEN"
            | "NCHI" | "SUBM" | "RESN" | "RESI"
            | "MARB" | "MARC" | "MARL" | "MARS" | "CENS" => {}
            tag if tag.starts_with('_') => {}
            _ => {}
        }
    }

    fam
}

fn build_event(children: &[Token]) -> Event {
    let date = find_first(children, 2, "DATE")
        .and_then(|t| t.value.as_ref())
        .map(|v| Date::parse(v));

    let place = find_first(children, 2, "PLAC")
        .and_then(|t| t.value.as_ref())
        .map(|v| Place::new(v));

    Event { date, place }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse::gedcom::lexer::tokenize;

    #[test]
    fn test_build_simple_individual() {
        let input = "\
0 HEAD
1 GEDC
2 VERS 5.5
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 1 Jan 1900
2 PLAC Boston, MA, USA
1 DEAT
2 DATE 31 Dec 1980
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.individuals.len(), 1);
        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.name.as_ref().unwrap().full, "John Smith");
        assert_eq!(indi.name.as_ref().unwrap().surname, Some("Smith".to_string()));
        assert_eq!(indi.sex, Some(Sex::Male));
        assert_eq!(indi.birth.as_ref().unwrap().date.as_ref().unwrap().year, Some(1900));
        assert_eq!(
            indi.birth.as_ref().unwrap().place.as_ref().unwrap().raw,
            "Boston, MA, USA"
        );
        assert_eq!(indi.death.as_ref().unwrap().date.as_ref().unwrap().year, Some(1980));
    }

    #[test]
    fn test_build_family_links() {
        let input = "\
0 HEAD
0 @I1@ INDI
1 NAME John /Smith/
1 FAMS @F1@
0 @I2@ INDI
1 NAME Jane /Doe/
1 FAMS @F1@
0 @I3@ INDI
1 NAME Bob /Smith/
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 25 Dec 1925
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.families.len(), 1);
        let fam = &tree.families["@F1@"];
        assert_eq!(fam.husband, Some("@I1@".to_string()));
        assert_eq!(fam.wife, Some("@I2@".to_string()));
        assert_eq!(fam.children, vec!["@I3@"]);
        assert_eq!(fam.marriage.as_ref().unwrap().date.as_ref().unwrap().year, Some(1925));

        // Individual links
        assert_eq!(tree.individuals["@I1@"].family_as_spouse, vec!["@F1@"]);
        assert_eq!(tree.individuals["@I3@"].family_as_child, vec!["@F1@"]);
    }

    #[test]
    fn test_build_header() {
        let input = "\
0 HEAD
1 SOUR FTM
1 GEDC
2 VERS 5.5
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.header.source, Some("FTM".to_string()));
        assert_eq!(tree.header.gedcom_version, Some("5.5".to_string()));
        assert_eq!(tree.header.gedcom_form, Some("LINEAGE-LINKED".to_string()));
        assert_eq!(tree.header.encoding, Some("UTF-8".to_string()));
    }

    #[test]
    fn test_givn_surn_override() {
        let input = "\
0 @I1@ INDI
1 NAME Robert Eugene /Williams/
2 SURN Williams
2 GIVN Robert Eugene";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        let name = indi.name.as_ref().unwrap();
        assert_eq!(name.given, Some("Robert Eugene".to_string()));
        assert_eq!(name.surname, Some("Williams".to_string()));
    }

    #[test]
    fn test_obje_file_extraction() {
        let input = "\
0 @I1@ INDI
1 NAME Bart /Simpson/
1 OBJE
2 FORM URL
2 FILE http://en.wikipedia.org/wiki/Bart_Simpson";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.media.len(), 1);
        assert_eq!(
            indi.media[0].file,
            Some("http://en.wikipedia.org/wiki/Bart_Simpson".to_string())
        );
    }

    #[test]
    fn test_unknown_tags_produce_warnings() {
        let input = "\
0 HEAD
0 @S1@ SOUR
1 TITL Some Source
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert!(tree.warnings.iter().any(|w| w.message.contains("SOUR")));
    }
}
