use crate::model::FamilyTree;

/// Supported field aliases for the `list` command.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ListField {
    Names,
    Surnames,
    Places,
    Dates,
}

impl ListField {
    /// Parse a field alias string. Returns None for unrecognized aliases.
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "names" | "name" => Some(ListField::Names),
            "surnames" | "surname" => Some(ListField::Surnames),
            "places" | "place" => Some(ListField::Places),
            "dates" | "date" => Some(ListField::Dates),
            _ => None,
        }
    }

    /// Return all valid alias names for error messages.
    pub fn valid_aliases() -> &'static str {
        "names, surnames, places, dates"
    }
}

/// Extract field values from a family tree.
/// Returns one value per occurrence (not deduplicated).
pub fn extract(tree: &FamilyTree, field: ListField) -> Vec<String> {
    let mut values = Vec::new();

    // Sort by xref for deterministic output
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort();

    for xref in xrefs {
        let indi = &tree.individuals[xref];
        match field {
            ListField::Names => {
                if let Some(ref name) = indi.name {
                    values.push(name.full.clone());
                }
            }
            ListField::Surnames => {
                if let Some(ref name) = indi.name {
                    if let Some(ref surname) = name.surname {
                        values.push(surname.clone());
                    }
                }
            }
            ListField::Places => {
                if let Some(ref birth) = indi.birth {
                    if let Some(ref place) = birth.place {
                        values.push(place.raw.clone());
                    }
                }
                if let Some(ref death) = indi.death {
                    if let Some(ref place) = death.place {
                        values.push(place.raw.clone());
                    }
                }
            }
            ListField::Dates => {
                if let Some(ref birth) = indi.birth {
                    if let Some(ref date) = birth.date {
                        values.push(date.raw.clone());
                    }
                }
                if let Some(ref death) = indi.death {
                    if let Some(ref date) = death.date {
                        values.push(date.raw.clone());
                    }
                }
            }
        }
    }

    // Also extract from family events (marriage dates/places)
    if matches!(field, ListField::Places | ListField::Dates) {
        let mut fam_xrefs: Vec<&String> = tree.families.keys().collect();
        fam_xrefs.sort();

        for fam_xref in fam_xrefs {
            let fam = &tree.families[fam_xref];
            if let Some(ref marriage) = fam.marriage {
                match field {
                    ListField::Places => {
                        if let Some(ref place) = marriage.place {
                            values.push(place.raw.clone());
                        }
                    }
                    ListField::Dates => {
                        if let Some(ref date) = marriage.date {
                            values.push(date.raw.clone());
                        }
                    }
                    _ => {}
                }
            }
        }
    }

    values
}

/// Deduplicate and sort values.
pub fn unique_sorted(mut values: Vec<String>) -> Vec<String> {
    values.sort();
    values.dedup();
    values
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
    fn test_list_names() {
        let tree = make_test_tree();
        let names = extract(&tree, ListField::Names);
        assert_eq!(names, vec!["John Smith", "Jane Doe", "Robert Smith"]);
    }

    #[test]
    fn test_list_surnames() {
        let tree = make_test_tree();
        let surnames = extract(&tree, ListField::Surnames);
        assert_eq!(surnames, vec!["Smith", "Doe", "Smith"]);
    }

    #[test]
    fn test_list_surnames_unique() {
        let tree = make_test_tree();
        let surnames = unique_sorted(extract(&tree, ListField::Surnames));
        assert_eq!(surnames, vec!["Doe", "Smith"]);
    }

    #[test]
    fn test_list_places() {
        let tree = make_test_tree();
        let places = extract(&tree, ListField::Places);
        // Birth + death places from individuals, plus marriage place from family
        assert!(places.contains(&"Boston, MA, USA".to_string()));
        assert!(places.contains(&"New York, NY, USA".to_string()));
        assert!(places.contains(&"Miami, FL, USA".to_string()));
    }

    #[test]
    fn test_list_dates() {
        let tree = make_test_tree();
        let dates = extract(&tree, ListField::Dates);
        assert!(dates.contains(&"1 Jan 1900".to_string()));
        assert!(dates.contains(&"31 Dec 1980".to_string()));
        assert!(dates.contains(&"25 Dec 1925".to_string()));
    }

    #[test]
    fn test_parse_field_aliases() {
        assert_eq!(ListField::parse("names"), Some(ListField::Names));
        assert_eq!(ListField::parse("name"), Some(ListField::Names));
        assert_eq!(ListField::parse("SURNAMES"), Some(ListField::Surnames));
        assert_eq!(ListField::parse("surname"), Some(ListField::Surnames));
        assert_eq!(ListField::parse("places"), Some(ListField::Places));
        assert_eq!(ListField::parse("place"), Some(ListField::Places));
        assert_eq!(ListField::parse("dates"), Some(ListField::Dates));
        assert_eq!(ListField::parse("date"), Some(ListField::Dates));
        assert_eq!(ListField::parse("unknown"), None);
    }

    #[test]
    fn test_unique_sorted() {
        let v = vec!["c".into(), "a".into(), "b".into(), "a".into()];
        assert_eq!(unique_sorted(v), vec!["a", "b", "c"]);
    }
}
