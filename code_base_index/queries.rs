// DEFAULT CODE
// use helix_db::helix_engine::graph_core::config::Config;

// pub fn config() -> Option<Config> {
//     None
// }

use chrono::{DateTime, Utc};
use heed3::RoTxn;
use helix_db::{
    embed, embed_async, exclude_field, field_addition_from_old_field, field_addition_from_value,
    field_remapping, field_type_cast,
    helix_engine::{
        traversal_core::{
            config::{Config, GraphConfig, VectorConfig},
            ops::{
                bm25::search_bm25::SearchBM25Adapter,
                g::G,
                in_::{in_::InAdapter, in_e::InEdgesAdapter, to_n::ToNAdapter, to_v::ToVAdapter},
                out::{
                    from_n::FromNAdapter, from_v::FromVAdapter, out::OutAdapter,
                    out_e::OutEdgesAdapter,
                },
                source::{
                    add_e::{AddEAdapter, EdgeType},
                    add_n::AddNAdapter,
                    e_from_id::EFromIdAdapter,
                    e_from_type::EFromTypeAdapter,
                    n_from_id::NFromIdAdapter,
                    n_from_index::NFromIndexAdapter,
                    n_from_type::NFromTypeAdapter,
                },
                util::{
                    dedup::DedupAdapter, drop::Drop, exist::Exist, filter_mut::FilterMut,
                    filter_ref::FilterRefAdapter, map::MapAdapter, order::OrderByAdapter,
                    paths::ShortestPathAdapter, props::PropsAdapter, range::RangeAdapter,
                    update::UpdateAdapter,
                },
                vectors::{
                    brute_force_search::BruteForceSearchVAdapter, insert::InsertVAdapter,
                    search::SearchVAdapter,
                },
            },
            traversal_value::{Traversable, TraversalValue},
        },
        types::GraphError,
        vector_core::vector::HVector,
    },
    helix_gateway::{
        embedding_providers::embedding_providers::{get_embedding_model, EmbeddingModel},
        mcp::mcp::{MCPHandler, MCPHandlerSubmission, MCPToolInput},
        router::router::{HandlerInput, IoContFn},
    },
    identifier_remapping, node_matches, props,
    protocol::{
        format::Format,
        remapping::{Remapping, RemappingMap, ResponseRemapping},
        response::Response,
        return_values::ReturnValue,
        value::{
            casting::{cast, CastType},
            Value,
        },
    },
    traversal_remapping,
    utils::{
        count::Count,
        filterable::Filterable,
        id::ID,
        items::{Edge, Node},
    },
    value_remapping,
};
use helix_macros::{handler, mcp_handler, migration, tool_call};
use sonic_rs::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use std::time::Instant;

pub fn config() -> Option<Config> {
    return Some(Config {
        vector_config: Some(VectorConfig {
            m: Some(16),
            ef_construction: Some(128),
            ef_search: Some(768),
        }),
        graph_config: Some(GraphConfig {
            secondary_indices: Some(vec![]),
        }),
        db_max_size_gb: Some(10),
        mcp: Some(true),
        bm25: Some(true),
        schema: Some(
            r#"{
  "schema": {
    "nodes": [
      {
        "name": "User",
        "properties": {
          "username": "String",
          "created_at": "Date",
          "id": "ID",
          "display_name": "String"
        }
      },
      {
        "name": "Repository",
        "properties": {
          "full_name": "String",
          "created_at": "Date",
          "extracted_at": "Date",
          "owner": "String",
          "name": "String",
          "id": "ID",
          "description": "String"
        }
      },
      {
        "name": "Folder",
        "properties": {
          "id": "ID",
          "name": "String",
          "extracted_at": "Date"
        }
      },
      {
        "name": "Entity",
        "properties": {
          "order": "I64",
          "end_byte": "I64",
          "text": "String",
          "id": "ID",
          "start_byte": "I64",
          "extracted_at": "Date",
          "entity_type": "String"
        }
      },
      {
        "name": "File",
        "properties": {
          "extracted_at": "Date",
          "name": "String",
          "extension": "String",
          "text": "String",
          "id": "ID"
        }
      }
    ],
    "vectors": [
      {
        "name": "EmbeddedCode",
        "properties": {
          "id": "ID",
          "vector": "Array(F64)"
        }
      }
    ],
    "edges": [
      {
        "name": "Repository_to_File",
        "from": "Repository",
        "to": "File",
        "properties": {}
      },
      {
        "name": "Entity_to_Entity",
        "from": "Entity",
        "to": "Entity",
        "properties": {}
      },
      {
        "name": "Repository_to_Folder",
        "from": "Repository",
        "to": "Folder",
        "properties": {}
      },
      {
        "name": "Folder_to_Folder",
        "from": "Folder",
        "to": "Folder",
        "properties": {}
      },
      {
        "name": "Entity_to_EmbeddedCode",
        "from": "Entity",
        "to": "EmbeddedCode",
        "properties": {}
      },
      {
        "name": "User_to_Repository",
        "from": "User",
        "to": "Repository",
        "properties": {
          "access_type": "String"
        }
      },
      {
        "name": "Folder_to_File",
        "from": "Folder",
        "to": "File",
        "properties": {}
      },
      {
        "name": "File_to_Entity",
        "from": "File",
        "to": "Entity",
        "properties": {}
      }
    ]
  },
  "queries": [
    {
      "name": "embedSuperEntity",
      "parameters": {
        "entity_id": "ID",
        "vector": "Array(F64)"
      },
      "returns": [
        "embedded_code"
      ]
    },
    {
      "name": "createSubEntity",
      "parameters": {
        "entity_id": "ID",
        "entity_type": "String",
        "order": "I64",
        "text": "String",
        "start_byte": "I64",
        "end_byte": "I64"
      },
      "returns": [
        "entity"
      ]
    },
    {
      "name": "getRepositoryById",
      "parameters": {
        "repo_id": "ID"
      },
      "returns": [
        "repo"
      ]
    },
    {
      "name": "createSuperFolder",
      "parameters": {
        "repo_name": "String",
        "owner": "String",
        "folder_name": "String"
      },
      "returns": [
        "folder"
      ]
    },
    {
      "name": "createSuperFile",
      "parameters": {
        "owner": "String",
        "repo_name": "String",
        "file_name": "String",
        "extension": "String",
        "text": "String"
      },
      "returns": [
        "file"
      ]
    },
    {
      "name": "createRepository",
      "parameters": {
        "username": "String",
        "full_name": "String",
        "repo_name": "String",
        "description": "String"
      },
      "returns": [
        "repo"
      ]
    },
    {
      "name": "getRepository",
      "parameters": {
        "repo_name": "String",
        "owner": "String"
      },
      "returns": [
        "repo"
      ]
    },
    {
      "name": "createUser",
      "parameters": {
        "display_name": "String",
        "username": "String"
      },
      "returns": [
        "user"
      ]
    },
    {
      "name": "getUser",
      "parameters": {
        "username": "String"
      },
      "returns": [
        "user"
      ]
    },
    {
      "name": "getAllUsers",
      "parameters": {},
      "returns": [
        "users"
      ]
    },
    {
      "name": "createSubFolder",
      "parameters": {
        "name": "String",
        "folder_id": "ID"
      },
      "returns": [
        "subfolder"
      ]
    },
    {
      "name": "createFile",
      "parameters": {
        "text": "String",
        "name": "String",
        "extension": "String",
        "folder_id": "ID"
      },
      "returns": [
        "file"
      ]
    },
    {
      "name": "getUserRepositories",
      "parameters": {
        "username": "String"
      },
      "returns": [
        "repos"
      ]
    },
    {
      "name": "createSuperEntity",
      "parameters": {
        "file_id": "ID",
        "order": "I64",
        "text": "String",
        "start_byte": "I64",
        "end_byte": "I64",
        "entity_type": "String"
      },
      "returns": [
        "entity"
      ]
    }
  ]
}"#
            .to_string(),
        ),
        embedding_model: Some("text-embedding-ada-002".to_string()),
        graphvis_node_label: Some("".to_string()),
    });
}

pub struct User {
    pub username: String,
    pub display_name: String,
    pub created_at: DateTime<Utc>,
}

pub struct Repository {
    pub owner: String,
    pub name: String,
    pub full_name: String,
    pub description: String,
    pub created_at: DateTime<Utc>,
    pub extracted_at: DateTime<Utc>,
}

pub struct Folder {
    pub name: String,
    pub extracted_at: DateTime<Utc>,
}

pub struct File {
    pub name: String,
    pub extension: String,
    pub text: String,
    pub extracted_at: DateTime<Utc>,
}

pub struct Entity {
    pub entity_type: String,
    pub start_byte: i64,
    pub end_byte: i64,
    pub order: i64,
    pub text: String,
    pub extracted_at: DateTime<Utc>,
}

pub struct User_to_Repository {
    pub from: User,
    pub to: Repository,
    pub access_type: String,
}

pub struct Repository_to_Folder {
    pub from: Repository,
    pub to: Folder,
}

pub struct Repository_to_File {
    pub from: Repository,
    pub to: File,
}

pub struct Folder_to_Folder {
    pub from: Folder,
    pub to: Folder,
}

pub struct Folder_to_File {
    pub from: Folder,
    pub to: File,
}

pub struct File_to_Entity {
    pub from: File,
    pub to: Entity,
}

pub struct Entity_to_Entity {
    pub from: Entity,
    pub to: Entity,
}

pub struct Entity_to_EmbeddedCode {
    pub from: Entity,
    pub to: EmbeddedCode,
}

pub struct EmbeddedCode {
    pub vector: Vec<f64>,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct embedSuperEntityInput {
    pub entity_id: ID,
    pub vector: Vec<f64>,
}
#[handler]
pub fn embedSuperEntity(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<embedSuperEntityInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let entity = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.entity_id)
        .collect_to_obj();
    let embedded_code = G::new_mut(Arc::clone(&db), &mut txn)
        .insert_v::<fn(&HVector, &RoTxn) -> bool>(&data.vector, "EmbeddedCode", None)
        .collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Entity_to_EmbeddedCode",
            None,
            entity.id(),
            embedded_code.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "embedded_code".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            embedded_code.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createSubEntityInput {
    pub entity_id: ID,
    pub entity_type: String,
    pub start_byte: i64,
    pub end_byte: i64,
    pub order: i64,
    pub text: String,
}
#[handler]
pub fn createSubEntity(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createSubEntityInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let parent = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.entity_id)
        .collect_to_obj();
    let entity = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("Entity", Some(props! { "extracted_at" => chrono::Utc::now().to_rfc3339(), "entity_type" => &data.entity_type, "end_byte" => &data.end_byte, "order" => &data.order, "text" => &data.text, "start_byte" => &data.start_byte }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Entity_to_Entity",
            None,
            parent.id(),
            entity.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "entity".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            entity.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct getRepositoryByIdInput {
    pub repo_id: ID,
}
#[handler]
pub fn getRepositoryById(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<getRepositoryByIdInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let txn = db.graph_env.read_txn().unwrap();
    let repo = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.repo_id)
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "repo".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            repo.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createSuperFolderInput {
    pub owner: String,
    pub repo_name: String,
    pub folder_name: String,
}
#[handler]
pub fn createSuperFolder(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createSuperFolderInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let repo = G::new(Arc::clone(&db), &txn)
        .n_from_type("Repository")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("owner")
                    .map_value_or(false, |v| *v == data.owner.clone())?)
            } else {
                Ok(false)
            }
        })
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("name")
                    .map_value_or(false, |v| *v == data.repo_name.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let folder = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("Folder", Some(props! { "name" => &data.folder_name, "extracted_at" => chrono::Utc::now().to_rfc3339() }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Repository_to_Folder",
            None,
            repo.id(),
            folder.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "folder".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            folder.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createSuperFileInput {
    pub owner: String,
    pub repo_name: String,
    pub file_name: String,
    pub extension: String,
    pub text: String,
}
#[handler]
pub fn createSuperFile(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createSuperFileInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let repo = G::new(Arc::clone(&db), &txn)
        .n_from_type("Repository")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("owner")
                    .map_value_or(false, |v| *v == data.owner.clone())?)
            } else {
                Ok(false)
            }
        })
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("name")
                    .map_value_or(false, |v| *v == data.repo_name.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let file = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("File", Some(props! { "extension" => &data.extension, "name" => &data.file_name, "extracted_at" => chrono::Utc::now().to_rfc3339(), "text" => &data.text }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Repository_to_File",
            None,
            repo.id(),
            file.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "file".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            file.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createRepositoryInput {
    pub username: String,
    pub repo_name: String,
    pub full_name: String,
    pub description: String,
}
#[handler]
pub fn createRepository(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createRepositoryInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let user = G::new(Arc::clone(&db), &txn)
        .n_from_type("User")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("username")
                    .map_value_or(false, |v| *v == data.username.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let repo = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("Repository", Some(props! { "created_at" => chrono::Utc::now().to_rfc3339(), "extracted_at" => chrono::Utc::now().to_rfc3339(), "full_name" => &data.full_name, "name" => &data.repo_name, "description" => &data.description, "owner" => &data.username }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "User_to_Repository",
            None,
            user.id(),
            repo.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "repo".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            repo.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct getRepositoryInput {
    pub owner: String,
    pub repo_name: String,
}
#[handler]
pub fn getRepository(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<getRepositoryInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let txn = db.graph_env.read_txn().unwrap();
    let repo = G::new(Arc::clone(&db), &txn)
        .n_from_type("Repository")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("owner")
                    .map_value_or(false, |v| *v == data.owner.clone())?)
            } else {
                Ok(false)
            }
        })
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("name")
                    .map_value_or(false, |v| *v == data.repo_name.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "repo".to_string(),
        ReturnValue::from_traversal_value_array_with_mixin(
            repo.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createUserInput {
    pub username: String,
    pub display_name: String,
}
#[handler]
pub fn createUser(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createUserInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let user = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("User", Some(props! { "display_name" => &data.display_name, "username" => &data.username, "created_at" => chrono::Utc::now().to_rfc3339() }), None).collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "user".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            user.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct getUserInput {
    pub username: String,
}
#[handler]
pub fn getUser(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<getUserInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let txn = db.graph_env.read_txn().unwrap();
    let user = G::new(Arc::clone(&db), &txn)
        .n_from_type("User")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("username")
                    .map_value_or(false, |v| *v == data.username.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "user".to_string(),
        ReturnValue::from_traversal_value_array_with_mixin(
            user.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct getAllUsersInput {}
#[handler]
pub fn getAllUsers(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<getAllUsersInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let txn = db.graph_env.read_txn().unwrap();
    let users = G::new(Arc::clone(&db), &txn)
        .n_from_type("User")
        .collect_to::<Vec<_>>();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "users".to_string(),
        ReturnValue::from_traversal_value_array_with_mixin(
            users.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createSubFolderInput {
    pub folder_id: ID,
    pub name: String,
}
#[handler]
pub fn createSubFolder(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createSubFolderInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let folder = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.folder_id)
        .collect_to_obj();
    let subfolder = G::new_mut(Arc::clone(&db), &mut txn)
        .add_n(
            "Folder",
            Some(
                props! { "name" => &data.name, "extracted_at" => chrono::Utc::now().to_rfc3339() },
            ),
            None,
        )
        .collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Folder_to_Folder",
            None,
            folder.id(),
            subfolder.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "subfolder".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            subfolder.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createFileInput {
    pub folder_id: ID,
    pub name: String,
    pub extension: String,
    pub text: String,
}
#[handler]
pub fn createFile(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createFileInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let folder = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.folder_id)
        .collect_to_obj();
    let file = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("File", Some(props! { "name" => &data.name, "text" => &data.text, "extension" => &data.extension, "extracted_at" => chrono::Utc::now().to_rfc3339() }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "Folder_to_File",
            None,
            folder.id(),
            file.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "file".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            file.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct getUserRepositoriesInput {
    pub username: String,
}
#[handler]
pub fn getUserRepositories(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<getUserRepositoriesInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let txn = db.graph_env.read_txn().unwrap();
    let user = G::new(Arc::clone(&db), &txn)
        .n_from_type("User")
        .filter_ref(|val, txn| {
            if let Ok(val) = val {
                Ok(G::new_from(Arc::clone(&db), &txn, val.clone())
                    .check_property("username")
                    .map_value_or(false, |v| *v == data.username.clone())?)
            } else {
                Ok(false)
            }
        })
        .collect_to::<Vec<_>>();
    let repos = G::new_from(Arc::clone(&db), &txn, user.clone())
        .out("User_to_Repository", &EdgeType::Node)
        .collect_to::<Vec<_>>();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "repos".to_string(),
        ReturnValue::from_traversal_value_array_with_mixin(
            repos.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}

#[derive(Serialize, Deserialize, Clone)]
pub struct createSuperEntityInput {
    pub file_id: ID,
    pub entity_type: String,
    pub start_byte: i64,
    pub end_byte: i64,
    pub order: i64,
    pub text: String,
}
#[handler]
pub fn createSuperEntity(input: HandlerInput) -> Result<Response, GraphError> {
    let db = Arc::clone(&input.graph.storage);
    let data = input
        .request
        .in_fmt
        .deserialize::<createSuperEntityInput>(&input.request.body)?;
    let mut remapping_vals = RemappingMap::new();
    let mut txn = db.graph_env.write_txn().unwrap();
    let file = G::new(Arc::clone(&db), &txn)
        .n_from_id(&data.file_id)
        .collect_to_obj();
    let entity = G::new_mut(Arc::clone(&db), &mut txn)
.add_n("Entity", Some(props! { "entity_type" => &data.entity_type, "start_byte" => &data.start_byte, "order" => &data.order, "extracted_at" => chrono::Utc::now().to_rfc3339(), "end_byte" => &data.end_byte, "text" => &data.text }), None).collect_to_obj();
    G::new_mut(Arc::clone(&db), &mut txn)
        .add_e(
            "File_to_Entity",
            None,
            file.id(),
            entity.id(),
            true,
            EdgeType::Node,
        )
        .collect_to_obj();
    let mut return_vals: HashMap<String, ReturnValue> = HashMap::new();
    return_vals.insert(
        "entity".to_string(),
        ReturnValue::from_traversal_value_with_mixin(
            entity.clone().clone(),
            remapping_vals.borrow_mut(),
        ),
    );

    txn.commit().unwrap();
    Ok(input.request.out_fmt.create_response(&return_vals))
}
