// helixdbproject/src/codebase_index/src/github_ingestion.rs
use anyhow::{Context, Result};
use reqwest::Client;
use serde::Deserialize;

// Struct to represent a file in the GitHub repository tree
#[derive(Deserialize, Debug)]
pub struct GitTreeItem {
    pub path: String,
    #[serde(rename = "type")]
    pub item_type: String, // "blob" for file, "tree" for directory
}

// Struct to represent the entire tree response from GitHub API
#[derive(Deserialize, Debug)]
struct GitTree {
    tree: Vec<GitTreeItem>,
}

// Struct for the file content API response
#[derive(Deserialize, Debug)]
struct FileContent {
    content: String,
    encoding: String,
}

// Fetches the list of all files in the main branch recursively
pub async fn fetch_repo_files(
    client: &Client,
    repo: &str,
    token: &str,
) -> Result<Vec<GitTreeItem>> {
    let url = format!(
        "https://api.github.com/repos/{}/git/trees/main?recursive=1",
        repo
    );

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("Accept", "application/vnd.github+json")
        .header("User-Agent", "helix-codebase-indexer") // GitHub requires a User-Agent
        .send()
        .await?
        .error_for_status()?; // Ensure we got a 2xx response

    let tree = response.json::<GitTree>().await?;

    // Filter out directories, keeping only files ("blobs")
    let files = tree
        .tree
        .into_iter()
        .filter(|item| item.item_type == "blob")
        .collect();

    Ok(files)
}

// Fetches the raw content of a single file and decodes it
pub async fn fetch_file_content(
    client: &Client,
    repo: &str,
    path: &str,
    token: &str,
) -> Result<String> {
    let url = format!("https://api.github.com/repos/{}/contents/{}", repo, path);

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("Accept", "application/vnd.github+json")
        .header("User-Agent", "helix-codebase-indexer")
        .send()
        .await?
        .error_for_status()?;

    let file_content: FileContent = response.json().await?;

    if file_content.encoding != "base64" {
        return Err(anyhow::anyhow!(
            "Unsupported encoding: {}",
            file_content.encoding
        ));
    }

    let decoded_content = base64::decode(&file_content.content.replace('\n', ""))
        .context("Failed to decode base64 content")?;

    Ok(String::from_utf8(decoded_content)?)
}
