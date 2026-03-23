use axum::{
    Router,
    routing::{get, post, put, delete},
    extract::Path,
    response::Json,
};
use serde_json::{json, Value};

async fn health() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

async fn list_users() -> Json<Value> {
    Json(json!([]))
}

async fn create_user() -> Json<Value> {
    Json(json!({"created": true}))
}

async fn get_user(Path(id): Path<u32>) -> Json<Value> {
    Json(json!({"id": id}))
}

async fn update_user(Path(id): Path<u32>) -> Json<Value> {
    Json(json!({"id": id, "updated": true}))
}

async fn delete_user(Path(id): Path<u32>) -> Json<Value> {
    Json(json!({"id": id, "deleted": true}))
}

async fn list_posts() -> Json<Value> {
    Json(json!([]))
}

async fn create_post() -> Json<Value> {
    Json(json!({"created": true}))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health))
        .route("/api/users", get(list_users))
        .route("/api/users", post(create_user))
        .route("/api/users/:id", get(get_user))
        .route("/api/users/:id", put(update_user))
        .route("/api/users/:id", delete(delete_user))
        .route("/api/posts", get(list_posts))
        .route("/api/posts", post(create_post));

    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
