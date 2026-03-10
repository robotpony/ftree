use ftree::parse::gedcom;
use ftree::render::markdown::MarkdownRenderer;
use ftree::render::Renderer;

fn parse_sample(filename: &str) -> ftree::model::FamilyTree {
    let path = format!("samples/{}", filename);
    let data = std::fs::read(&path).unwrap_or_else(|e| panic!("Failed to read {}: {}", path, e));
    gedcom::parse(&data).unwrap_or_else(|e| panic!("Failed to parse {}: {}", path, e))
}

#[test]
fn test_parse_test_details() {
    let tree = parse_sample("test_details.ged");

    assert_eq!(tree.individuals.len(), 3);
    assert_eq!(tree.families.len(), 1);

    // John Smith
    let john = &tree.individuals["@I1@"];
    assert_eq!(john.name.as_ref().unwrap().full, "John Smith");
    assert_eq!(john.name.as_ref().unwrap().given, Some("John".to_string()));
    assert_eq!(
        john.name.as_ref().unwrap().surname,
        Some("Smith".to_string())
    );
    assert_eq!(john.sex, Some(ftree::model::Sex::Male));
    assert_eq!(
        john.birth.as_ref().unwrap().date.as_ref().unwrap().year,
        Some(1900)
    );
    assert_eq!(
        john.birth
            .as_ref()
            .unwrap()
            .place
            .as_ref()
            .unwrap()
            .raw,
        "Boston, MA, USA"
    );
    assert_eq!(
        john.death.as_ref().unwrap().date.as_ref().unwrap().year,
        Some(1980)
    );

    // Jane Doe
    let jane = &tree.individuals["@I2@"];
    assert_eq!(jane.name.as_ref().unwrap().full, "Jane Doe");
    assert_eq!(jane.sex, Some(ftree::model::Sex::Female));

    // Robert Smith (child)
    let robert = &tree.individuals["@I3@"];
    assert_eq!(robert.family_as_child, vec!["@F1@"]);

    // Family
    let fam = &tree.families["@F1@"];
    assert_eq!(fam.husband, Some("@I1@".to_string()));
    assert_eq!(fam.wife, Some("@I2@".to_string()));
    assert_eq!(fam.children, vec!["@I3@"]);
    assert_eq!(
        fam.marriage.as_ref().unwrap().date.as_ref().unwrap().year,
        Some(1925)
    );
}

#[test]
fn test_parse_simpsons() {
    let tree = parse_sample("Simpsons Cartoon.ged");

    // Should have parsed individuals with descriptive xrefs
    assert!(tree.individuals.contains_key("@Homer_Simpson@"));
    assert!(tree.individuals.contains_key("@Bart_Simpson@"));
    assert!(tree.individuals.contains_key("@Abraham_Simpson@"));

    let homer = &tree.individuals["@Homer_Simpson@"];
    assert_eq!(homer.name.as_ref().unwrap().full, "Homer Simpson");
    assert_eq!(homer.sex, Some(ftree::model::Sex::Male));

    // Homer has OBJE with URL
    assert!(homer.media.len() >= 1);

    // Bart has OBJE with URL
    let bart = &tree.individuals["@Bart_Simpson@"];
    assert!(bart.media.len() >= 1);
    assert!(bart.media[0]
        .file
        .as_ref()
        .unwrap()
        .contains("wikipedia.org"));

    // Verify family structure
    assert!(!tree.families.is_empty());
}

#[test]
fn test_parse_harry_potter() {
    let tree = parse_sample("Harry Potter.ged");

    assert!(tree.individuals.contains_key("@I00001@"));

    let harry = &tree.individuals["@I00001@"];
    assert_eq!(harry.name.as_ref().unwrap().full, "Harry Potter");
    assert_eq!(harry.sex, Some(ftree::model::Sex::Male));

    // Should have a reasonable number of individuals
    assert!(tree.individuals.len() > 10);
    assert!(!tree.families.is_empty());
}

#[test]
fn test_parse_windows_dos() {
    let tree = parse_sample("Microsoft Windows DOS OS2.ged");

    // Should parse without panicking despite unusual name formats
    assert!(!tree.individuals.is_empty());
    assert!(!tree.families.is_empty());

    // Check that complex names are handled
    let win20 = &tree.individuals["@I00001@"];
    assert!(win20.name.is_some());
}

#[test]
fn test_parse_utf16_sample() {
    let tree = parse_sample("555SAMPLE16LE.GED");

    // Should successfully decode UTF-16 LE and parse
    assert!(!tree.individuals.is_empty());
    assert!(!tree.families.is_empty());

    // Verify a known individual
    assert!(tree.individuals.contains_key("@I1@"));
    let robert = &tree.individuals["@I1@"];
    assert_eq!(
        robert.name.as_ref().unwrap().full,
        "Robert Eugene Williams"
    );

    // Verify header was parsed
    assert!(tree.header.gedcom_version.is_some());
}

#[test]
fn test_all_samples_parse_without_error() {
    // Ensure every sample file can be parsed without panicking
    let samples = [
        "test_details.ged",
        "Simpsons Cartoon.ged",
        "Harry Potter.ged",
        "Microsoft Windows DOS OS2.ged",
        "555SAMPLE16LE.GED",
    ];

    for sample in &samples {
        let tree = parse_sample(sample);
        // Every file should produce at least some data
        assert!(
            !tree.individuals.is_empty() || !tree.families.is_empty(),
            "{} produced no individuals or families",
            sample
        );
    }
}

// --- Markdown export integration tests ---

fn export_to_tempdir(filename: &str) -> (ftree::model::FamilyTree, tempfile::TempDir) {
    let tree = parse_sample(filename);
    let dir = tempfile::tempdir().expect("Failed to create temp dir");
    let renderer = MarkdownRenderer;
    renderer.render(&tree, dir.path()).expect("Render failed");
    (tree, dir)
}

#[test]
fn test_markdown_export_creates_files() {
    let (tree, dir) = export_to_tempdir("test_details.ged");

    // Should create one .md file per individual
    let files: Vec<_> = std::fs::read_dir(dir.path())
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map(|ext| ext == "md").unwrap_or(false))
        .collect();

    assert_eq!(files.len(), tree.individuals.len());
}

#[test]
fn test_markdown_export_file_content() {
    let (_tree, dir) = export_to_tempdir("test_details.ged");

    let john_path = dir.path().join("John Smith.md");
    assert!(john_path.exists(), "John Smith.md should exist");

    let content = std::fs::read_to_string(&john_path).unwrap();

    // YAML front-matter
    assert!(content.starts_with("---\n"));
    assert!(content.contains("name: John Smith"));
    assert!(content.contains("sex: male"));
    assert!(content.contains("birth_date: 1 Jan 1900"));

    // Body with wikilinks
    assert!(content.contains("# John Smith"));
    assert!(content.contains("[[Jane Doe]]"));
    assert!(content.contains("[[Robert Smith]]"));
}

#[test]
fn test_markdown_export_parent_links() {
    let (_tree, dir) = export_to_tempdir("test_details.ged");

    let robert_path = dir.path().join("Robert Smith.md");
    let content = std::fs::read_to_string(&robert_path).unwrap();

    assert!(content.contains("## Parents"));
    assert!(content.contains("[[John Smith]]"));
    assert!(content.contains("[[Jane Doe]]"));
}

#[test]
fn test_markdown_export_simpsons() {
    let (_tree, dir) = export_to_tempdir("Simpsons Cartoon.ged");

    let homer_path = dir.path().join("Homer Simpson.md");
    assert!(homer_path.exists());

    let content = std::fs::read_to_string(&homer_path).unwrap();
    assert!(content.contains("[[Marge Simpson]]"));
    assert!(content.contains("[[Bart Simpson]]"));
    assert!(content.contains("[[Abraham Simpson]]"));
    // Media links
    assert!(content.contains("wikipedia.org"));
}

#[test]
fn test_markdown_export_utf16_sample() {
    let (_tree, dir) = export_to_tempdir("555SAMPLE16LE.GED");

    let robert_path = dir.path().join("Robert Eugene Williams.md");
    assert!(robert_path.exists());

    let content = std::fs::read_to_string(&robert_path).unwrap();
    assert!(content.contains("name: Robert Eugene Williams"));
}

#[test]
fn test_markdown_export_windows_dos_special_chars() {
    let (_tree, dir) = export_to_tempdir("Microsoft Windows DOS OS2.ged");

    // All files should have been created without errors
    let files: Vec<_> = std::fs::read_dir(dir.path())
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map(|ext| ext == "md").unwrap_or(false))
        .collect();

    assert!(!files.is_empty());

    // No filenames should contain problematic characters
    for file in &files {
        let name = file.file_name();
        let name_str = name.to_string_lossy();
        assert!(
            !name_str.contains('/') && !name_str.contains(':') && !name_str.contains('*'),
            "Filename contains illegal character: {}",
            name_str
        );
    }
}

#[test]
fn test_markdown_export_all_samples() {
    let samples = [
        "test_details.ged",
        "Simpsons Cartoon.ged",
        "Harry Potter.ged",
        "Microsoft Windows DOS OS2.ged",
        "555SAMPLE16LE.GED",
    ];

    for sample in &samples {
        let (tree, dir) = export_to_tempdir(sample);

        let files: Vec<_> = std::fs::read_dir(dir.path())
            .unwrap()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().extension().map(|ext| ext == "md").unwrap_or(false))
            .collect();

        assert_eq!(
            files.len(),
            tree.individuals.len(),
            "{}: file count mismatch",
            sample
        );

        // Every file should be valid UTF-8 and contain YAML front-matter
        for file in &files {
            let content = std::fs::read_to_string(file.path()).unwrap();
            assert!(
                content.starts_with("---\n"),
                "{}: {} missing front-matter",
                sample,
                file.file_name().to_string_lossy()
            );
        }
    }
}
