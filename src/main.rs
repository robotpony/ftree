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

        /// Output format
        #[arg(long, default_value = "md")]
        format: String,

        /// Output path (directory for md, file for other formats)
        #[arg(short, long)]
        output: Option<PathBuf>,
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
                other => {
                    anyhow::bail!("Unsupported format: {}. Available: md", other);
                }
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
    println!("Individuals: {}", tree.individuals.len());
    println!("Families:    {}", tree.families.len());

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

    if !tree.warnings.is_empty() {
        println!();
        println!("Warnings: {}", tree.warnings.len());
        for warning in &tree.warnings {
            println!("  - {}", warning);
        }
    }
}
