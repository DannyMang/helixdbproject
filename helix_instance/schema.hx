// User represents a GitHub account/organization that owns repositories
N::User {
    username: String,
    created_at: Date DEFAULT NOW
}

// Repository (formerly Root) represents a single GitHub repository
N::Repository {
    owner: String,         // GitHub username of the owner
    name: String,          // Repository name
    full_name: String,     // Combined as "owner/name"
    extracted_at: Date DEFAULT NOW
}

N::Folder {
    name: String,
    extracted_at: Date DEFAULT NOW
}

N::File {
    name: String,
    extension: String,
    text: String,
    extracted_at: Date DEFAULT NOW
}

N::Entity {
    entity_type: String,
    start_byte: I64,
    end_byte: I64,
    order: I64,
    text: String,
    extracted_at: Date DEFAULT NOW
}

// Link between User and Repository
E::User_to_Repository {
    From: User,
    To: Repository,
    Properties: {
        access_type: String DEFAULT "owner"
    }
}

// Updated from Root_to_Folder
E::Repository_to_Folder {
    From: Repository,
    To: Folder,
    Properties: {
    }
}

// Updated from Root_to_File
E::Repository_to_File {
    From: Repository,
    To: File,
    Properties: {
    }
}

E::Folder_to_Folder {
    From: Folder,
    To: Folder,
    Properties: {
    }
}

E::Folder_to_File {
    From: Folder,
    To: File,
    Properties: {
    }
}

E::File_to_Entity {
    From: File,
    To: Entity,
    Properties: {
    }
}

E::Entity_to_Entity {
    From: Entity,
    To: Entity,
    Properties: {
    }
}

E::Entity_to_EmbeddedCode {
    From: Entity,
    To: EmbeddedCode,
    Properties: {
    }
}

V::EmbeddedCode {
    vector: [F64]
}
