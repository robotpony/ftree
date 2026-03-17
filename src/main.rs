use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

use ftree::render::Renderer;

#[derive(Parser)]
#[command(name = "ftree", about = "Read and convert GEDCOM genealogy files")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Check a GEDCOM file for validity and statistics
    Check {
        /// Path to the GEDCOM file
        file: PathBuf,
    },
    /// Export family tree to various formats
    Export {
        /// Path to the GEDCOM file
        file: PathBuf,

        /// Output format (md, csv, svg, html)
        #[arg(long, default_value = "md")]
        format: String,

        /// Output path (directory for md, file for csv)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// View family tree as ASCII art in the terminal
    View {
        /// Path to the GEDCOM file
        file: PathBuf,

        /// Layout orientation (topdown, horizontal)
        #[arg(long, default_value = "horizontal")]
        layout: String,

        /// Output to file instead of stdout
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// List field values extracted from a GEDCOM file
    List {
        /// Path to the GEDCOM file
        file: PathBuf,

        /// Field to extract (names, surnames, places, dates)
        field: String,

        /// Output only unique values, sorted alphabetically
        #[arg(long)]
        unique: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Check { file } => {
            let tree = load_tree(&file)?;
            print_check_report(&tree, &file);
            Ok(())
        }
        Commands::Export {
            file,
            format,
            output,
        } => {
            let tree = load_tree(&file)?;

            match format.as_str() {
                "md" => {
                    let output_dir = output.unwrap_or_else(|| {
                        file.with_extension("")
                    });
                    let renderer = ftree::render::markdown::MarkdownRenderer;
                    renderer
                        .render(&tree, &output_dir)
                        .with_context(|| format!("Failed to export to {}", output_dir.display()))?;
                    println!(
                        "Exported {} individuals to {}",
                        tree.individuals.len(),
                        output_dir.display()
                    );
                }
                "csv" => {
                    let output_file = output.unwrap_or_else(|| {
                        file.with_extension("csv")
                    });
                    let renderer = ftree::render::csv::CsvRenderer;
                    renderer
                        .render(&tree, &output_file)
                        .with_context(|| format!("Failed to export to {}", output_file.display()))?;
                    println!(
                        "Exported {} individuals to {}",
                        tree.individuals.len(),
                        output_file.display()
                    );
                }
                "svg" => {
                    let output_file = output.unwrap_or_else(|| {
                        file.with_extension("svg")
                    });
                    let renderer = ftree::render::svg::SvgRenderer;
                    renderer
                        .render(&tree, &output_file)
                        .with_context(|| format!("Failed to export to {}", output_file.display()))?;
                    println!(
                        "Exported {} individuals to {}",
                        tree.individuals.len(),
                        output_file.display()
                    );
                }
                "html" => {
                    let output_file = output.unwrap_or_else(|| {
                        file.with_extension("html")
                    });
                    let renderer = ftree::render::html::HtmlRenderer;
                    renderer
                        .render(&tree, &output_file)
                        .with_context(|| format!("Failed to export to {}", output_file.display()))?;
                    println!(
                        "Exported {} individuals to {}",
                        tree.individuals.len(),
                        output_file.display()
                    );
                }
                other => {
                    anyhow::bail!("Unsupported format: {}. Available: md, csv, svg, html", other);
                }
            }
            Ok(())
        }
        Commands::View {
            file,
            layout,
            output,
        } => {
            let ascii_layout = ftree::render::ascii::Layout::parse(&layout)
                .ok_or_else(|| {
                    anyhow::anyhow!(
                        "Unknown layout: '{}'. Available: topdown, horizontal",
                        layout
                    )
                })?;

            let tree = load_tree(&file)?;
            let renderer = ftree::render::ascii::AsciiRenderer { layout: ascii_layout };

            match output {
                Some(path) => {
                    renderer
                        .render(&tree, &path)
                        .with_context(|| format!("Failed to write to {}", path.display()))?;
                    println!("Wrote tree to {}", path.display());
                }
                None => {
                    print!("{}", renderer.render_to_string(&tree));
                }
            }
            Ok(())
        }
        Commands::List {
            file,
            field,
            unique,
        } => {
            let list_field = ftree::render::list::ListField::parse(&field)
                .ok_or_else(|| {
                    anyhow::anyhow!(
                        "Unknown field: '{}'. Available: {}",
                        field,
                        ftree::render::list::ListField::valid_aliases()
                    )
                })?;

            let tree = load_tree(&file)?;
            let mut values = ftree::render::list::extract(&tree, list_field);

            if unique {
                values = ftree::render::list::unique_sorted(values);
            }

            for value in &values {
                println!("{}", value);
            }
            Ok(())
        }
    }
}

fn load_tree(file: &PathBuf) -> Result<ftree::model::FamilyTree> {
    let data = std::fs::read(file).with_context(|| format!("Failed to read {}", file.display()))?;
    ftree::parse::gedcom::parse(&data)
        .with_context(|| format!("Failed to parse {}", file.display()))
}

fn print_check_report(tree: &ftree::model::FamilyTree, path: &std::path::Path) {
    println!("File: {}", path.display());

    if let Some(ref source) = tree.header.source {
        println!("Source: {}", source);
    }
    if let Some(ref version) = tree.header.gedcom_version {
        println!("GEDCOM version: {}", version);
    }
    if let Some(ref encoding) = tree.header.encoding {
        println!("Encoding: {}", encoding);
    }

    println!();
    println!("Individuals:  {}", tree.individuals.len());
    println!("Families:     {}", tree.families.len());
    println!("Sources:      {}", tree.sources.len());
    println!("Repositories: {}", tree.repositories.len());

    let missing_names = tree
        .individuals
        .values()
        .filter(|i| i.name.is_none())
        .count();
    let missing_birth = tree
        .individuals
        .values()
        .filter(|i| i.birth.is_none())
        .count();
    let missing_death = tree
        .individuals
        .values()
        .filter(|i| i.death.is_none())
        .count();
    let missing_sex = tree
        .individuals
        .values()
        .filter(|i| i.sex.is_none())
        .count();

    println!();
    println!("Missing names:       {}", missing_names);
    println!("Missing birth dates: {}", missing_birth);
    println!("Missing death dates: {}", missing_death);
    println!("Missing sex:         {}", missing_sex);

    let lint_warnings = ftree::lint::lint(tree);
    if !lint_warnings.is_empty() {
        println!();
        println!("Lint issues: {}", lint_warnings.len());
        for warning in &lint_warnings {
            println!("  - {}", warning);
        }
    }

    if !tree.warnings.is_empty() {
        println!();
        println!("Parse warnings: {}", tree.warnings.len());
        for warning in &tree.warnings {
            println!("  - {}", warning);
        }
    }
}
