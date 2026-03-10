pub mod builder;
pub mod encoding;
pub mod lexer;

use crate::model::FamilyTree;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParseError {
    #[error("Failed to decode file: {0}")]
    EncodingError(String),
}

/// Parse raw bytes from a GEDCOM file into a FamilyTree.
pub fn parse(input: &[u8]) -> Result<FamilyTree, ParseError> {
    let decoded = encoding::decode(input);
    let tokens = lexer::tokenize(&decoded.text);
    let mut tree = builder::build(&tokens);

    // Store detected encoding in header if not already set from CHAR declaration
    if tree.header.encoding.is_none() {
        tree.header.encoding = Some(format!("{:?}", decoded.encoding));
    }

    Ok(tree)
}
