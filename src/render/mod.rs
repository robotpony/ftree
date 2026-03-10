pub mod markdown;

use std::path::Path;
use thiserror::Error;

use crate::model::FamilyTree;

#[derive(Error, Debug)]
pub enum RenderError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Render error: {0}")]
    Other(String),
}

/// Trait for output renderers.
pub trait Renderer {
    /// Render the family tree to the given output path.
    ///
    /// For single-file formats, `output` is a file path.
    /// For multi-file formats (like Markdown), `output` is a directory.
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError>;
}
