use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

use crate::model::{FamilyTree, Individual, NoteRef, Sex};
use crate::render::{RenderError, Renderer};
use crate::render::svg::render_svg;

/// Standalone HTML family tree viewer renderer.
///
/// Generates a single HTML file with embedded CSS (light/dark theme support)
/// and JavaScript for filtering. Includes a summary table and individual detail sections.
pub struct HtmlRenderer {
    /// When true, the SVG family tree diagram is embedded at the top of the page.
    pub embed_svg: bool,
}

impl Renderer for HtmlRenderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError> {
        let content = render_html(tree, self.embed_svg);
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(output, content)?;
        Ok(())
    }
}

/// Generate the full HTML document.
pub fn render_html(tree: &FamilyTree, embed_svg: bool) -> String {
    let mut out = String::new();

    // Sort individuals by name for deterministic output
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort_by_key(|x| {
        tree.individuals[*x].display_name().to_lowercase()
    });

    out.push_str("<!DOCTYPE html>\n");
    out.push_str("<html lang=\"en\">\n");
    out.push_str("<head>\n");
    out.push_str("  <meta charset=\"UTF-8\">\n");
    out.push_str("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n");
    out.push_str("  <title>Family Tree</title>\n");
    out.push_str(CSS);
    out.push_str("</head>\n");
    out.push_str("<body>\n");

    // Header
    let _ = writeln!(
        out,
        "  <header>\n    <h1>Family Tree</h1>\n    <p class=\"stats\">{} individuals &middot; {} families</p>\n  </header>",
        tree.individuals.len(),
        tree.families.len()
    );

    // Embedded SVG diagram (optional)
    if embed_svg {
        let svg = render_svg(tree);
        out.push_str("  <section class=\"svg-section\">\n");
        out.push_str("    <h2>Family Tree Diagram</h2>\n");
        out.push_str("    <div class=\"svg-container\">\n");
        out.push_str(&svg);
        out.push_str("    </div>\n");
        out.push_str("  </section>\n");
    }

    // Search bar
    out.push_str(r#"  <div class="search-bar">
    <input type="text" id="search" placeholder="Search by name&hellip;" oninput="filterTable(this.value)" aria-label="Search individuals">
  </div>
"#);

    // Summary table
    out.push_str("  <section class=\"table-section\">\n");
    out.push_str("    <table id=\"individuals-table\">\n");
    out.push_str("      <thead>\n        <tr>\n");
    out.push_str("          <th>Name</th><th>Sex</th><th>Born</th><th>Died</th><th>Father</th><th>Mother</th>\n");
    out.push_str("        </tr>\n      </thead>\n      <tbody>\n");

    for xref in &xrefs {
        let indi = &tree.individuals[*xref];
        let anchor = xref_to_id(xref);
        let name = html_escape(indi.display_name());
        let sex = sex_label(&indi.sex);
        let birth = event_year_str(indi.birth.as_ref());
        let death = event_year_str(indi.death.as_ref());
        let (father, mother) = parents(indi, tree);
        let father_html = person_link(&father, tree);
        let mother_html = person_link(&mother, tree);

        let sex_class = sex_class(&indi.sex);

        let _ = writeln!(
            out,
            "        <tr data-name=\"{}\">\n          <td><a href=\"#{anchor}\">{name}</a></td>\n          <td class=\"{sex_class}\">{sex}</td><td>{birth}</td><td>{death}</td><td>{father_html}</td><td>{mother_html}</td>\n        </tr>",
            indi.display_name().to_lowercase()
        );
    }

    out.push_str("      </tbody>\n    </table>\n  </section>\n");

    // Individual detail cards
    out.push_str("  <section class=\"details\">\n");

    for xref in &xrefs {
        let indi = &tree.individuals[*xref];
        render_individual_section(&mut out, indi, xref, tree);
    }

    out.push_str("  </section>\n");

    // JavaScript for search
    out.push_str(JS);

    out.push_str("</body>\n</html>\n");
    out
}

fn render_individual_section(out: &mut String, indi: &Individual, xref: &str, tree: &FamilyTree) {
    let anchor = xref_to_id(xref);
    let name = html_escape(indi.display_name());
    let sex_class = sex_class(&indi.sex);

    let _ = writeln!(out, "    <article class=\"person-card {sex_class}\" id=\"{anchor}\">");
    let _ = writeln!(out, "      <h2>{name}</h2>");

    // Vital events
    let mut has_vitals = false;
    let mut vitals = String::new();

    if let Some(ref e) = indi.birth {
        push_field(&mut vitals, "Born", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref e) = indi.christening {
        push_field(&mut vitals, "Christened", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref e) = indi.adoption {
        push_field(&mut vitals, "Adopted", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref e) = indi.death {
        push_field(&mut vitals, "Died", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref e) = indi.burial {
        push_field(&mut vitals, "Buried", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref e) = indi.residence {
        push_field(&mut vitals, "Residence", &format_event(e));
        has_vitals = true;
    }
    if let Some(ref v) = indi.occupation {
        push_field(&mut vitals, "Occupation", v);
        has_vitals = true;
    }
    if let Some(ref v) = indi.education {
        push_field(&mut vitals, "Education", v);
        has_vitals = true;
    }
    if let Some(ref v) = indi.title {
        push_field(&mut vitals, "Title", v);
        has_vitals = true;
    }

    if has_vitals {
        let _ = writeln!(out, "      <dl class=\"vitals\">{}</dl>", vitals);
    }

    // Parents
    let (father_xref, mother_xref) = parents(indi, tree);
    if father_xref.is_some() || mother_xref.is_some() {
        out.push_str("      <section class=\"relations\">\n        <h3>Parents</h3>\n        <ul>\n");
        if let Some(ref fx) = father_xref {
            let _ = writeln!(out, "          <li><span class=\"label\">Father:</span> {}</li>", person_link(&Some(fx.clone()), tree));
        }
        if let Some(ref mx) = mother_xref {
            let _ = writeln!(out, "          <li><span class=\"label\">Mother:</span> {}</li>", person_link(&Some(mx.clone()), tree));
        }
        out.push_str("        </ul>\n      </section>\n");
    }

    // Spouse families
    for fam_xref in &indi.family_as_spouse {
        if let Some(fam) = tree.families.get(fam_xref) {
            let spouse_xref = if fam.husband.as_deref() == Some(xref) {
                fam.wife.as_deref()
            } else {
                fam.husband.as_deref()
            };

            out.push_str("      <section class=\"relations\">\n        <h3>Spouse &amp; Children</h3>\n        <ul>\n");

            if let Some(sx) = spouse_xref {
                let _ = writeln!(out, "          <li><span class=\"label\">Spouse:</span> {}</li>", person_link(&Some(sx.to_string()), tree));
            }
            if let Some(ref e) = fam.engagement {
                push_li(out, "Engaged", &format_event(e));
            }
            if let Some(ref e) = fam.marriage {
                push_li(out, "Married", &format_event(e));
            }
            if let Some(ref e) = fam.divorce {
                push_li(out, "Divorced", &format_event(e));
            }
            if let Some(ref e) = fam.annulment {
                push_li(out, "Annulled", &format_event(e));
            }

            for child_xref in &fam.children {
                let _ = writeln!(out, "          <li><span class=\"label\">Child:</span> {}</li>", person_link(&Some(child_xref.clone()), tree));
            }

            out.push_str("        </ul>\n      </section>\n");
        }
    }

    // Sources
    if !indi.source_citations.is_empty() {
        out.push_str("      <section class=\"sources\">\n        <h3>Sources</h3>\n        <ul>\n");
        for citation in &indi.source_citations {
            let title = tree
                .sources
                .get(&citation.source_xref)
                .map(|s| s.display_title())
                .unwrap_or(&citation.source_xref);
            let text = match &citation.page {
                Some(page) => format!("{} ({})", html_escape(title), html_escape(page)),
                None => html_escape(title),
            };
            let _ = writeln!(out, "          <li>{}</li>", text);
        }
        out.push_str("        </ul>\n      </section>\n");
    }

    // Notes
    if !indi.notes.is_empty() {
        out.push_str("      <section class=\"notes\">\n        <h3>Notes</h3>\n");
        for note in &indi.notes {
            let text = resolve_note_text(note, tree);
            if let Some(text) = text {
                let _ = writeln!(out, "        <p>{}</p>", html_escape(text));
            }
        }
        out.push_str("      </section>\n");
    }

    out.push_str("    </article>\n");
}

// ── Helpers ──────────────────────────────────────────────────────────────────

fn xref_to_id(xref: &str) -> String {
    xref.trim_matches('@')
        .chars()
        .map(|c| if c.is_alphanumeric() || c == '-' { c } else { '_' })
        .collect()
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn sex_label(sex: &Option<Sex>) -> &'static str {
    match sex {
        Some(Sex::Male) => "M",
        Some(Sex::Female) => "F",
        Some(Sex::Unknown) | None => "—",
    }
}

fn sex_class(sex: &Option<Sex>) -> &'static str {
    match sex {
        Some(Sex::Male) => "male",
        Some(Sex::Female) => "female",
        _ => "",
    }
}

fn event_year_str(event: Option<&crate::model::Event>) -> String {
    event
        .and_then(|e| e.date.as_ref())
        .map(|d| d.raw.clone())
        .unwrap_or_default()
}

fn format_event(event: &crate::model::Event) -> String {
    match (&event.date, &event.place) {
        (Some(d), Some(p)) => format!("{}, {}", d, p),
        (Some(d), None) => d.to_string(),
        (None, Some(p)) => p.to_string(),
        (None, None) => String::new(),
    }
}

/// Returns (father_xref, mother_xref) for an individual.
fn parents(indi: &Individual, tree: &FamilyTree) -> (Option<String>, Option<String>) {
    for fam_xref in &indi.family_as_child {
        if let Some(fam) = tree.families.get(fam_xref) {
            return (fam.husband.clone(), fam.wife.clone());
        }
    }
    (None, None)
}

/// Render a person as a hyperlink (or plain text if not found).
fn person_link(xref: &Option<String>, tree: &FamilyTree) -> String {
    match xref {
        Some(x) => {
            let anchor = xref_to_id(x);
            let name = tree
                .individuals
                .get(x)
                .map(|i| html_escape(i.display_name()))
                .unwrap_or_else(|| html_escape(x));
            format!("<a href=\"#{anchor}\">{name}</a>")
        }
        None => String::new(),
    }
}

fn push_field(out: &mut String, label: &str, value: &str) {
    if !value.is_empty() {
        let _ = write!(
            out,
            "<dt>{}</dt><dd>{}</dd>",
            label,
            html_escape(value)
        );
    }
}

fn push_li(out: &mut String, label: &str, value: &str) {
    if !value.is_empty() {
        let _ = writeln!(
            out,
            "          <li><span class=\"label\">{label}:</span> {}</li>",
            html_escape(value)
        );
    }
}

fn resolve_note_text<'a>(note: &'a NoteRef, tree: &'a FamilyTree) -> Option<&'a str> {
    if let Some(ref text) = note.text {
        return Some(text.as_str());
    }
    if let Some(ref xref) = note.xref {
        return tree.notes.get(xref).map(|n| n.text.as_str());
    }
    None
}

// ── Embedded CSS ─────────────────────────────────────────────────────────────

const CSS: &str = r#"  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #f9fafb;
      --surface: #ffffff;
      --border: #e5e7eb;
      --text: #111827;
      --text-muted: #6b7280;
      --accent: #3b82f6;
      --male-bg: #eff6ff;
      --male-border: #bfdbfe;
      --female-bg: #fdf2f8;
      --female-border: #fbcfe8;
      --radius: 8px;
      --shadow: 0 1px 3px rgba(0,0,0,.08);
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111827;
        --surface: #1f2937;
        --border: #374151;
        --text: #f9fafb;
        --text-muted: #9ca3af;
        --accent: #60a5fa;
        --male-bg: #1e3a5f;
        --male-border: #3b82f6;
        --female-bg: #4a1942;
        --female-border: #ec4899;
      }
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      padding: 24px 16px;
      max-width: 1100px;
      margin: 0 auto;
    }

    header { margin-bottom: 24px; }
    h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 4px; }
    .stats { color: var(--text-muted); }

    .search-bar { margin-bottom: 16px; }
    .search-bar input {
      width: 100%;
      max-width: 360px;
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      color: var(--text);
      font-size: 14px;
    }
    .search-bar input:focus { outline: 2px solid var(--accent); border-color: transparent; }

    /* Table */
    .table-section { overflow-x: auto; margin-bottom: 40px; }
    table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); }
    th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: var(--border); font-weight: 600; color: var(--text-muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: color-mix(in srgb, var(--accent) 6%, transparent); }
    td.male { color: #3b82f6; }
    td.female { color: #ec4899; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* Detail cards */
    .details { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
    .person-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
    }
    .person-card.male  { border-left: 3px solid #3b82f6; background: var(--male-bg); }
    .person-card.female { border-left: 3px solid #ec4899; background: var(--female-bg); }
    .person-card h2 { font-size: 1rem; font-weight: 700; margin-bottom: 12px; }

    /* Vitals definition list */
    dl.vitals { display: grid; grid-template-columns: auto 1fr; gap: 2px 12px; margin-bottom: 12px; }
    dt { font-weight: 600; color: var(--text-muted); font-size: 12px; padding-top: 2px; }
    dd { color: var(--text); }

    /* Relations & sources sections */
    .relations, .sources, .notes { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
    .relations h3, .sources h3, .notes h3 { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); margin-bottom: 6px; }
    .relations ul, .sources ul { list-style: none; }
    .relations li, .sources li { padding: 2px 0; }
    .label { font-weight: 600; color: var(--text-muted); margin-right: 4px; }
    .notes p { font-size: 13px; color: var(--text); line-height: 1.6; }

    /* SVG diagram section */
    .svg-section { margin-bottom: 40px; }
    .svg-section h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; }
    .svg-container {
      overflow-x: auto;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      box-shadow: var(--shadow);
    }
    .svg-container svg { display: block; }

    /* Hidden rows (search) */
    tr.hidden { display: none; }
  </style>
"#;

// ── Embedded JavaScript ───────────────────────────────────────────────────────

const JS: &str = r#"  <script>
    function filterTable(query) {
      var q = query.toLowerCase().trim();
      var rows = document.querySelectorAll('#individuals-table tbody tr');
      rows.forEach(function(row) {
        var name = row.getAttribute('data-name') || '';
        row.classList.toggle('hidden', q !== '' && !name.includes(q));
      });
    }
  </script>
"#;

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
            place: Some(Place::new("Boston, MA")),
        });
        john.death = Some(Event {
            date: Some(Date::parse("31 Dec 1980")),
            place: None,
        });
        john.occupation = Some("Engineer".to_string());
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
            place: None,
        });

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    #[test]
    fn test_html_is_valid_document() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.starts_with("<!DOCTYPE html>"));
        assert!(html.contains("<html lang=\"en\">"));
        assert!(html.ends_with("</html>\n"));
        assert!(html.contains("</body>"));
    }

    #[test]
    fn test_html_contains_names() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("John Smith"));
        assert!(html.contains("Jane Doe"));
        assert!(html.contains("Robert Smith"));
    }

    #[test]
    fn test_html_contains_dates() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("1 Jan 1900"));
        assert!(html.contains("31 Dec 1980"));
    }

    #[test]
    fn test_html_contains_occupation() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("Engineer"));
    }

    #[test]
    fn test_html_contains_marriage() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("25 Dec 1925"));
    }

    #[test]
    fn test_html_has_anchors_for_individuals() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        // Each individual should have an anchor id
        assert!(html.contains("id=\"I1\"") || html.contains("id=\"I1_\""));
    }

    #[test]
    fn test_html_has_links_between_relatives() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        // Parent links should reference correct anchors
        assert!(html.contains("href=\"#I1\"") || html.contains("href=\"#"));
    }

    #[test]
    fn test_html_escapes_special_chars() {
        assert_eq!(html_escape("A & B"), "A &amp; B");
        assert_eq!(html_escape("<tag>"), "&lt;tag&gt;");
    }

    #[test]
    fn test_html_empty_tree() {
        let tree = FamilyTree::new();
        let html = render_html(&tree, false);

        assert!(html.starts_with("<!DOCTYPE html>"));
        assert!(html.contains("0 individuals"));
    }

    #[test]
    fn test_html_has_search_input() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("<input"));
        assert!(html.contains("filterTable"));
    }

    #[test]
    fn test_html_has_dark_mode_css() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("prefers-color-scheme: dark"));
    }

    #[test]
    fn test_xref_to_id() {
        assert_eq!(xref_to_id("@I1@"), "I1");
        assert_eq!(xref_to_id("@Homer_Simpson@"), "Homer_Simpson");
    }

    #[test]
    fn test_html_contains_stats() {
        let tree = make_test_tree();
        let html = render_html(&tree, false);

        assert!(html.contains("3 individuals"));
        assert!(html.contains("1 families") || html.contains("1 famil"));
    }

    #[test]
    fn test_html_note_rendering() {
        let mut tree = make_test_tree();
        tree.individuals.get_mut("@I1@").unwrap().notes.push(NoteRef {
            text: Some("A notable person.".to_string()),
            xref: None,
        });

        let html = render_html(&tree, false);
        assert!(html.contains("A notable person."));
    }

    #[test]
    fn test_html_embed_svg() {
        let tree = make_test_tree();
        let html_no_svg = render_html(&tree, false);
        let html_with_svg = render_html(&tree, true);

        assert!(!html_no_svg.contains("<section class=\"svg-section\""), "no SVG section without flag");
        assert!(html_with_svg.contains("<section class=\"svg-section\""), "SVG section present with flag");
        assert!(html_with_svg.contains("<svg "), "SVG element embedded");
    }
}
