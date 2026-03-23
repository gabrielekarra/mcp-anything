use rocket::serde::json::Json;
use rocket::serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
#[serde(crate = "rocket::serde")]
struct User {
    id: u32,
    name: String,
}

#[derive(Serialize, Deserialize)]
#[serde(crate = "rocket::serde")]
struct NewUser {
    name: String,
}

#[get("/health")]
fn health() -> &'static str {
    "ok"
}

#[get("/api/users")]
fn list_users() -> Json<Vec<User>> {
    Json(vec![])
}

#[get("/api/users/<id>")]
fn get_user(id: u32) -> Json<User> {
    Json(User { id, name: "Alice".into() })
}

#[post("/api/users", data = "<user>")]
fn create_user(user: Json<NewUser>) -> Json<User> {
    Json(User { id: 1, name: user.name.clone() })
}

#[put("/api/users/<id>", data = "<user>")]
fn update_user(id: u32, user: Json<NewUser>) -> Json<User> {
    Json(User { id, name: user.name.clone() })
}

#[delete("/api/users/<id>")]
fn delete_user(id: u32) -> &'static str {
    "deleted"
}

#[launch]
fn rocket() -> _ {
    rocket::build().mount("/", routes![
        health,
        list_users,
        get_user,
        create_user,
        update_user,
        delete_user,
    ])
}
