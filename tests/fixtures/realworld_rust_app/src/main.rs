use actix_web::{web, App, HttpServer, HttpResponse, Responder};

async fn list_articles() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!([]))
}

async fn create_article() -> impl Responder {
    HttpResponse::Created().json(serde_json::json!({}))
}

async fn get_article(slug: web::Path<String>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({}))
}

async fn update_article(slug: web::Path<String>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({}))
}

async fn delete_article(slug: web::Path<String>) -> impl Responder {
    HttpResponse::NoContent().finish()
}

async fn get_profile(username: web::Path<String>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({}))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/api/articles", web::get().to(list_articles))
            .route("/api/articles", web::post().to(create_article))
            .route("/api/articles/{slug}", web::get().to(get_article))
            .route("/api/articles/{slug}", web::put().to(update_article))
            .route("/api/articles/{slug}", web::delete().to(delete_article))
            .route("/api/profiles/{username}", web::get().to(get_profile))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
