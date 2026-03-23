use warp::Filter;

async fn list_users() -> Result<impl warp::Reply, warp::Rejection> {
    Ok(warp::reply::json(&vec![] as &Vec<String>))
}

async fn create_user() -> Result<impl warp::Reply, warp::Rejection> {
    Ok(warp::reply::json(&"created"))
}

async fn list_products() -> Result<impl warp::Reply, warp::Rejection> {
    Ok(warp::reply::json(&vec![] as &Vec<String>))
}

async fn health() -> Result<impl warp::Reply, warp::Rejection> {
    Ok(warp::reply::json(&"ok"))
}

#[tokio::main]
async fn main() {
    let users_get = warp::path("users")
        .and(warp::get())
        .and_then(list_users);

    let users_post = warp::path("users")
        .and(warp::post())
        .and_then(create_user);

    let products = warp::path("products")
        .and(warp::get())
        .and_then(list_products);

    let health_route = warp::path("health")
        .and(warp::get())
        .and_then(health);

    let routes = users_get.or(users_post).or(products).or(health_route);

    warp::serve(routes).run(([127, 0, 0, 1], 3030)).await;
}
