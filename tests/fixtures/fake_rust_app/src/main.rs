use actix_web::{web, App, HttpServer, HttpResponse, get, post, put, delete};

#[get("/health")]
async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status": "ok"}))
}

#[get("/api/users")]
async fn list_users() -> HttpResponse {
    HttpResponse::Ok().json(vec![] as Vec<String>)
}

#[get("/api/users/{id}")]
async fn get_user(path: web::Path<(i32,)>) -> HttpResponse {
    let id = path.into_inner().0;
    HttpResponse::Ok().json(serde_json::json!({"id": id}))
}

#[post("/api/users")]
async fn create_user(body: web::Json<CreateUser>) -> HttpResponse {
    HttpResponse::Created().json(serde_json::json!({"name": body.name}))
}

#[put("/api/users/{id}")]
async fn update_user(path: web::Path<(i32,)>, body: web::Json<CreateUser>) -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"id": path.into_inner().0}))
}

#[delete("/api/users/{id}")]
async fn delete_user(path: web::Path<(i32,)>) -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"deleted": true}))
}

struct CreateUser {
    pub name: String,
    pub email: String,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(health)
            .service(list_users)
            .service(get_user)
            .service(create_user)
            .service(update_user)
            .service(delete_user)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
