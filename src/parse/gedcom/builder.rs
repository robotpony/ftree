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
            "SOUR" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let source = build_source(xref, &tokens[i..end]);
                    tree.sources.insert(xref.clone(), source);
                }
                i = end;
            }
            "REPO" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let repo = build_repository(xref, &tokens[i..end]);
                    tree.repositories.insert(xref.clone(), repo);
                }
                i = end;
            }
            "OBJE" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let obj = build_multimedia_object(xref, &tokens[i..end]);
                    tree.multimedia_objects.insert(xref.clone(), obj);
                }
                i = end;
            }
            "NOTE" => {
                let end = find_record_end(tokens, i);
                if let Some(ref xref) = token.xref {
                    let note = build_note(xref, &tokens[i..end]);
                    tree.notes.insert(xref.clone(), note);
                }
                i = end;
            }
            "SUBM" | "TRLR" | "SUBN" => {
                i = find_record_end(tokens, i);
            }
            _ => {
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
            "BURI" => {
                let children = get_children(tokens, idx);
                indi.burial = Some(build_event(children));
            }
            "CHR" => {
                let children = get_children(tokens, idx);
                indi.christening = Some(build_event(children));
            }
            "ADOP" => {
                let children = get_children(tokens, idx);
                indi.adoption = Some(build_event(children));
            }
            "RESI" => {
                let children = get_children(tokens, idx);
                indi.residence = Some(build_event(children));
            }
            "OCCU" => {
                if let Some(ref v) = token.value {
                    indi.occupation = Some(v.clone());
                }
            }
            "EDUC" => {
                if let Some(ref v) = token.value {
                    indi.education = Some(v.clone());
                }
            }
            "TITL" => {
                if let Some(ref v) = token.value {
                    indi.title = Some(v.clone());
                }
            }
            "NOTE" => {
                let note_ref = build_note_ref(tokens, idx);
                indi.notes.push(note_ref);
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
                // Pointer form: 1 OBJE @O1@ — references a top-level OBJE record
                if token.value.as_ref().is_some_and(|v| v.starts_with('@')) {
                    indi.media.push(MediaRef {
                        file: None,
                        xref: token.value.clone(),
                    });
                } else {
                    // Inline form: FILE is a level-2 child
                    let children = get_children(tokens, idx);
                    let file = find_first(children, 2, "FILE")
                        .and_then(|t| t.value.clone());
                    indi.media.push(MediaRef { file, xref: None });
                }
            }
            "SOUR" => {
                // Inline source citation (pointer form: SOUR @S1@)
                if token.value.as_ref().is_some_and(|v| v.starts_with('@')) {
                    let citation = build_source_citation(tokens, idx);
                    indi.source_citations.push(citation);
                }
            }
            // Skip known but unhandled tags silently
            "CHAN" | "REFN" | "RIN" | "AFN" | "RFN" | "ALIA"
            | "EVEN" | "BAPM" | "RELI" | "NATI"
            | "CAST" | "DSCR" | "IDNO" | "NCHI"
            | "NMR" | "PROP" | "SSN" | "FACT"
            | "CREM" | "CONF" | "GRAD" | "RETI" | "WILL"
            | "PROB" | "CENS" | "EMIG" | "IMMI" | "NATU"
            | "SUBM" | "ANCI" | "DESI" | "RESN" | "MARR" => {}
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
            "DIV" => {
                let children = get_children(tokens, idx);
                fam.divorce = Some(build_event(children));
            }
            "ENGA" => {
                let children = get_children(tokens, idx);
                fam.engagement = Some(build_event(children));
            }
            "ANUL" => {
                let children = get_children(tokens, idx);
                fam.annulment = Some(build_event(children));
            }
            "NOTE" => {
                let note_ref = build_note_ref(tokens, idx);
                fam.notes.push(note_ref);
            }
            // Skip known but unhandled family tags
            "CHAN" | "REFN" | "RIN" | "SOUR" | "OBJE"
            | "DIVF" | "EVEN"
            | "NCHI" | "SUBM" | "RESN" | "RESI"
            | "MARB" | "MARC" | "MARL" | "MARS" | "CENS" => {}
            tag if tag.starts_with('_') => {}
            _ => {}
        }
    }

    fam
}

fn build_multimedia_object(xref: &str, tokens: &[Token]) -> MultimediaObject {
    let mut obj = MultimediaObject::new(xref.to_string());

    for (idx, token) in tokens.iter().enumerate() {
        if token.level != 1 {
            continue;
        }

        match token.tag.as_str() {
            "FILE" => {
                obj.file = token.value.clone();
                // Look for TITL at level 2 under FILE
                let children = get_children(tokens, idx);
                if let Some(titl) = find_first(children, 2, "TITL") {
                    obj.title = titl.value.clone();
                }
            }
            _ => {}
        }
    }

    obj
}

fn build_source(xref: &str, tokens: &[Token]) -> Source {
    let mut source = Source::new(xref.to_string());

    for token in tokens.iter() {
        if token.level != 1 {
            continue;
        }

        match token.tag.as_str() {
            "TITL" => {
                source.title = token.value.clone();
            }
            "AUTH" => {
                source.author = token.value.clone();
            }
            "PUBL" => {
                source.publisher = token.value.clone();
            }
            "ABBR" => {
                source.abbreviation = token.value.clone();
            }
            "TEXT" => {
                source.text = token.value.clone();
            }
            "REPO" => {
                // Pointer to repository record
                source.repository_xref = token.value.clone();
            }
            // Silently skip other known substructures
            "DATA" | "REFN" | "RIN" | "CHAN" | "NOTE" | "OBJE" => {}
            _ if token.tag.starts_with('_') => {}
            _ => {}
        }
    }

    source
}

fn build_repository(xref: &str, tokens: &[Token]) -> Repository {
    let mut repo = Repository::new(xref.to_string());

    for token in tokens.iter() {
        if token.level != 1 {
            continue;
        }

        match token.tag.as_str() {
            "NAME" => {
                repo.name = token.value.clone();
            }
            // Silently skip address, notes, etc.
            "ADDR" | "REFN" | "RIN" | "CHAN" | "NOTE" | "PHON" | "EMAIL" | "FAX" | "WWW" => {}
            _ if token.tag.starts_with('_') => {}
            _ => {}
        }
    }

    repo
}

fn build_source_citation(tokens: &[Token], parent_idx: usize) -> SourceCitation {
    let children = get_children(tokens, parent_idx);
    let page = find_first(children, 2, "PAGE")
        .and_then(|t| t.value.clone());
    let quality = find_first(children, 2, "QUAY")
        .and_then(|t| t.value.as_ref())
        .and_then(|v| v.trim().parse::<u8>().ok());

    SourceCitation {
        source_xref: tokens[parent_idx].value.clone().unwrap_or_default(),
        page,
        quality,
    }
}

/// Collect multi-line text from a token value + CONT/CONC children.
fn collect_text(tokens: &[Token], parent_idx: usize) -> String {
    let mut result = tokens[parent_idx].value.clone().unwrap_or_default();
    let children = get_children(tokens, parent_idx);
    for token in children {
        match token.tag.as_str() {
            "CONT" => {
                result.push('\n');
                if let Some(ref v) = token.value {
                    result.push_str(v);
                }
            }
            "CONC" => {
                if let Some(ref v) = token.value {
                    result.push_str(v);
                }
            }
            _ => {}
        }
    }
    result
}

/// Build a top-level NOTE record.
fn build_note(xref: &str, tokens: &[Token]) -> crate::model::Note {
    // The text is on the level-0 NOTE token (index 0) plus CONT/CONC at level 1
    let text = collect_text(tokens, 0);
    crate::model::Note::new(xref.to_string(), text)
}

/// Build a NoteRef from an inline NOTE tag in an INDI or FAM record.
fn build_note_ref(tokens: &[Token], parent_idx: usize) -> crate::model::NoteRef {
    let value = tokens[parent_idx].value.clone();
    // Pointer form: NOTE @N1@
    if value.as_ref().is_some_and(|v| v.starts_with('@')) {
        crate::model::NoteRef {
            text: None,
            xref: value,
        }
    } else {
        // Inline form: collect text with CONT/CONC
        let text = collect_text(tokens, parent_idx);
        crate::model::NoteRef {
            text: if text.is_empty() { None } else { Some(text) },
            xref: None,
        }
    }
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
    fn test_obje_pointer_form() {
        let input = "\
0 @O1@ OBJE
1 FILE
2 TITL Portrait Photo
0 @I1@ INDI
1 NAME Jane /Smith/
1 OBJE @O1@
2 _PRIM Y
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.multimedia_objects.len(), 1);
        let obj = &tree.multimedia_objects["@O1@"];
        assert_eq!(obj.title, Some("Portrait Photo".to_string()));
        assert_eq!(obj.file, None);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.media.len(), 1);
        assert_eq!(indi.media[0].xref, Some("@O1@".to_string()));
        assert_eq!(indi.media[0].file, None);
    }

    #[test]
    fn test_obje_top_level_with_file() {
        let input = "\
0 @O1@ OBJE
1 FILE http://example.com/photo.jpg
2 TITL Family Photo
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let obj = &tree.multimedia_objects["@O1@"];
        assert_eq!(obj.file, Some("http://example.com/photo.jpg".to_string()));
        assert_eq!(obj.title, Some("Family Photo".to_string()));
    }

    #[test]
    fn test_obje_no_warnings() {
        let input = "\
0 @O1@ OBJE
1 FILE photo.jpg
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert!(
            !tree.warnings.iter().any(|w| w.message.contains("OBJE")),
            "Top-level OBJE should not produce warnings"
        );
    }

    #[test]
    fn test_marr_in_indi_no_warning() {
        let input = "\
0 @I1@ INDI
1 NAME John /Smith/
1 MARR
2 DATE 1 Jan 1900
2 PLAC Boston, MA
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert!(
            !tree.warnings.iter().any(|w| w.message.contains("MARR")),
            "MARR in INDI should be silently skipped, not warned"
        );
    }

    #[test]
    fn test_unknown_tags_produce_warnings() {
        let input = "\
0 HEAD
0 @X1@ XYZZ
1 DATA something
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert!(tree.warnings.iter().any(|w| w.message.contains("XYZZ")));
    }

    #[test]
    fn test_build_source_record() {
        let input = "\
0 HEAD
0 @S1@ SOUR
1 TITL Wikipedia Image Source
1 AUTH John Doe
1 PUBL Self-published
1 ABBR Wiki
1 TEXT Some text from the source
1 REPO @R1@
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.sources.len(), 1);
        let source = &tree.sources["@S1@"];
        assert_eq!(source.title, Some("Wikipedia Image Source".to_string()));
        assert_eq!(source.author, Some("John Doe".to_string()));
        assert_eq!(source.publisher, Some("Self-published".to_string()));
        assert_eq!(source.abbreviation, Some("Wiki".to_string()));
        assert_eq!(source.text, Some("Some text from the source".to_string()));
        assert_eq!(source.repository_xref, Some("@R1@".to_string()));
    }

    #[test]
    fn test_build_source_title_only() {
        let input = "\
0 @S1@ SOUR
1 TITL My Source";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let source = &tree.sources["@S1@"];
        assert_eq!(source.display_title(), "My Source");
    }

    #[test]
    fn test_build_source_no_title_falls_back_to_abbr() {
        let input = "\
0 @S1@ SOUR
1 ABBR ShortName";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let source = &tree.sources["@S1@"];
        assert_eq!(source.display_title(), "ShortName");
    }

    #[test]
    fn test_build_repository_record() {
        let input = "\
0 HEAD
0 @R1@ REPO
1 NAME Family History Library
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.repositories.len(), 1);
        let repo = &tree.repositories["@R1@"];
        assert_eq!(repo.name, Some("Family History Library".to_string()));
    }

    #[test]
    fn test_inline_source_citation() {
        let input = "\
0 @S1@ SOUR
1 TITL Birth Records
0 @I1@ INDI
1 NAME John /Smith/
1 SOUR @S1@
2 PAGE Sec. 2, p. 45
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.source_citations.len(), 1);
        assert_eq!(indi.source_citations[0].source_xref, "@S1@");
        assert_eq!(indi.source_citations[0].page, Some("Sec. 2, p. 45".to_string()));
    }

    #[test]
    fn test_inline_source_citation_no_page() {
        let input = "\
0 @I1@ INDI
1 NAME Jane /Doe/
1 SOUR @S1@
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.source_citations.len(), 1);
        assert_eq!(indi.source_citations[0].source_xref, "@S1@");
        assert_eq!(indi.source_citations[0].page, None);
    }

    #[test]
    fn test_sour_and_repo_no_warnings() {
        let input = "\
0 HEAD
0 @S1@ SOUR
1 TITL Some Source
0 @R1@ REPO
1 NAME Some Repo
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        // SOUR and REPO should not produce warnings
        assert!(
            !tree.warnings.iter().any(|w| w.message.contains("SOUR") || w.message.contains("REPO")),
            "SOUR/REPO should not produce warnings, but got: {:?}",
            tree.warnings
        );
    }

    #[test]
    fn test_multiple_sources() {
        let input = "\
0 @S1@ SOUR
1 TITL Source One
0 @S2@ SOUR
1 TITL Source Two
0 @I1@ INDI
1 NAME Bob /Jones/
1 SOUR @S1@
1 SOUR @S2@
2 PAGE p. 10
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.sources.len(), 2);
        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.source_citations.len(), 2);
        assert_eq!(indi.source_citations[0].source_xref, "@S1@");
        assert_eq!(indi.source_citations[1].source_xref, "@S2@");
        assert_eq!(indi.source_citations[1].page, Some("p. 10".to_string()));
    }

    #[test]
    fn test_source_citation_quay() {
        let input = "\
0 @S1@ SOUR
1 TITL Some Source
0 @I1@ INDI
1 NAME John /Doe/
1 SOUR @S1@
2 PAGE p. 5
2 QUAY 3
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.source_citations[0].page, Some("p. 5".to_string()));
        assert_eq!(indi.source_citations[0].quality, Some(3));
    }

    #[test]
    fn test_individual_burial_and_christening() {
        let input = "\
0 @I1@ INDI
1 NAME Jane /Smith/
1 CHR
2 DATE 15 Jan 1900
2 PLAC Springfield, IL
1 BURI
2 DATE 5 Jun 1985
2 PLAC Oak Hill Cemetery
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        let chr = indi.christening.as_ref().unwrap();
        assert_eq!(chr.date.as_ref().unwrap().year, Some(1900));
        assert_eq!(chr.place.as_ref().unwrap().raw, "Springfield, IL");
        let buri = indi.burial.as_ref().unwrap();
        assert_eq!(buri.date.as_ref().unwrap().year, Some(1985));
        assert_eq!(buri.place.as_ref().unwrap().raw, "Oak Hill Cemetery");
    }

    #[test]
    fn test_individual_adoption_and_residence() {
        let input = "\
0 @I1@ INDI
1 NAME Bob /Jones/
1 ADOP
2 DATE 1920
1 RESI
2 DATE 1940
2 PLAC Chicago, IL
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.adoption.as_ref().unwrap().date.as_ref().unwrap().year, Some(1920));
        assert_eq!(indi.residence.as_ref().unwrap().date.as_ref().unwrap().year, Some(1940));
        assert_eq!(indi.residence.as_ref().unwrap().place.as_ref().unwrap().raw, "Chicago, IL");
    }

    #[test]
    fn test_individual_attributes() {
        let input = "\
0 @I1@ INDI
1 NAME Alice /Brown/
1 OCCU Baker
1 EDUC University of Chicago
1 TITL Dr.
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.occupation, Some("Baker".to_string()));
        assert_eq!(indi.education, Some("University of Chicago".to_string()));
        assert_eq!(indi.title, Some("Dr.".to_string()));
    }

    #[test]
    fn test_family_divorce_engagement_annulment() {
        let input = "\
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 ENGA
2 DATE 1 Jun 1925
1 MARR
2 DATE 25 Dec 1925
1 DIV
2 DATE 1950
1 ANUL
2 DATE 1951
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let fam = &tree.families["@F1@"];
        assert_eq!(fam.engagement.as_ref().unwrap().date.as_ref().unwrap().year, Some(1925));
        assert_eq!(fam.marriage.as_ref().unwrap().date.as_ref().unwrap().year, Some(1925));
        assert_eq!(fam.divorce.as_ref().unwrap().date.as_ref().unwrap().year, Some(1950));
        assert_eq!(fam.annulment.as_ref().unwrap().date.as_ref().unwrap().year, Some(1951));
    }

    #[test]
    fn test_note_record_inline() {
        let input = "\
0 @N1@ NOTE This is line one.
1 CONT This is line two.
1 CONC Continued on same line.
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        assert_eq!(tree.notes.len(), 1);
        let note = &tree.notes["@N1@"];
        assert_eq!(note.text, "This is line one.\nThis is line two.Continued on same line.");
    }

    #[test]
    fn test_inline_note_in_individual() {
        let input = "\
0 @I1@ INDI
1 NAME Bob /Jones/
1 NOTE He was a sailor.
2 CONT Also an adventurer.
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.notes.len(), 1);
        assert_eq!(indi.notes[0].text, Some("He was a sailor.\nAlso an adventurer.".to_string()));
        assert_eq!(indi.notes[0].xref, None);
    }

    #[test]
    fn test_pointer_note_in_individual() {
        let input = "\
0 @N1@ NOTE A shared note.
0 @I1@ INDI
1 NAME Bob /Jones/
1 NOTE @N1@
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let indi = &tree.individuals["@I1@"];
        assert_eq!(indi.notes.len(), 1);
        assert_eq!(indi.notes[0].xref, Some("@N1@".to_string()));
        assert_eq!(indi.notes[0].text, None);
        assert_eq!(tree.notes["@N1@"].text, "A shared note.");
    }

    #[test]
    fn test_note_in_family() {
        let input = "\
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 NOTE Married in secret.
0 TRLR";
        let tokens = tokenize(input);
        let tree = build(&tokens);

        let fam = &tree.families["@F1@"];
        assert_eq!(fam.notes.len(), 1);
        assert_eq!(fam.notes[0].text, Some("Married in secret.".to_string()));
    }
}
