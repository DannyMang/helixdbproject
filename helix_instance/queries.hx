// User Management
QUERY createUser(username: String, display_name: String) =>
    user <- AddN<User>({username: username, display_name: display_name})
    RETURN user

QUERY getUser(username: String) =>
    user <- N<User>::WHERE(_::{username}::EQ(username))
    RETURN user

QUERY getAllUsers() =>
    users <- N<User>
    RETURN users

// Repository Management
QUERY createRepository(username: String, repo_name: String, full_name: String, description: String) =>
    user <- N<User>::WHERE(_::{username}::EQ(username))
    repo <- AddN<Repository>({
        owner: username,
        name: repo_name,
        full_name: full_name,
        description: description
    })
    AddE<User_to_Repository>()::From(user)::To(repo)
    RETURN repo

QUERY getRepository(owner: String, repo_name: String) =>
    repo <- N<Repository>::WHERE(_::{owner}::EQ(owner))::WHERE(_::{name}::EQ(repo_name))
    RETURN repo

QUERY getUserRepositories(username: String) =>
    user <- N<User>::WHERE(_::{username}::EQ(username))
    repos <- user::Out<User_to_Repository>
    RETURN repos

// Create Folders - scoped to repository
QUERY createSuperFolder(owner: String, repo_name: String, folder_name: String) =>
    repo <- N<Repository>::WHERE(_::{owner}::EQ(owner))::WHERE(_::{name}::EQ(repo_name))
    folder <- AddN<Folder>({name: folder_name})
    AddE<Repository_to_Folder>()::From(repo)::To(folder)
    RETURN folder

QUERY createSubFolder(folder_id: ID, name: String) =>
    folder <- N<Folder>(folder_id)
    subfolder <- AddN<Folder>({name: name})
    AddE<Folder_to_Folder>()::From(folder)::To(subfolder)
    RETURN subfolder

// Create Files - scoped to repository
QUERY createSuperFile(owner: String, repo_name: String, file_name: String, extension: String, text: String) =>
    repo <- N<Repository>::WHERE(_::{owner}::EQ(owner))::WHERE(_::{name}::EQ(repo_name))
    file <- AddN<File>({name: file_name, extension: extension, text: text})
    AddE<Repository_to_File>()::From(repo)::To(file)
    RETURN file

QUERY createFile(folder_id: ID, name: String, extension: String, text: String) =>
    folder <- N<Folder>(folder_id)
    file <- AddN<File>({name: name, extension: extension, text: text})
    AddE<Folder_to_File>()::From(folder)::To(file)
    RETURN file

// Create Entities
QUERY createSuperEntity(file_id: ID, entity_type: String, start_byte: I64, end_byte: I64, order: I64, text: String) =>
    file <- N<File>(file_id)
    entity <- AddN<Entity>({entity_type: entity_type, start_byte: start_byte, end_byte: end_byte, order: order, text: text})
    AddE<File_to_Entity>()::From(file)::To(entity)
    RETURN entity

QUERY embedSuperEntity(entity_id: ID, vector: [F64]) =>
    entity <- N<Entity>(entity_id)
    embedded_code <- AddV<EmbeddedCode>(vector)
    AddE<Entity_to_EmbeddedCode>()::From(entity)::To(embedded_code)
    RETURN embedded_code

QUERY createSubEntity(entity_id: ID, entity_type: String, start_byte: I64, end_byte: I64, order: I64, text: String) =>
    parent <- N<Entity>(entity_id)
    entity <- AddN<Entity>({entity_type: entity_type, start_byte: start_byte, end_byte: end_byte, order: order, text: text})
    AddE<Entity_to_Entity>()::From(parent)::To(entity)
    RETURN entity

QUERY getRepositoryById(repo_id: ID) =>
    repo <- N<Repository>(repo_id)
    RETURN repo

//QUERY getFolderRepository(folder_id: ID) =>
    //repo <- N<Repository>::WHERE(_::{owner}::EQ(owner))::WHERE(_::{name}::EQ(repo_name))
    //RETURN repo
