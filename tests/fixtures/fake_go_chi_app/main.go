package main

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
)

type User struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

func listUsers(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode([]User{})
}

func createUser(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(User{ID: 1, Name: "Alice"})
}

func getUser(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	json.NewEncoder(w).Encode(map[string]string{"id": id})
}

func updateUser(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	json.NewEncoder(w).Encode(map[string]string{"id": id})
}

func deleteUser(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]bool{"deleted": true})
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func main() {
	r := chi.NewRouter()

	r.Get("/health", healthCheck)
	r.Get("/api/users", listUsers)
	r.Post("/api/users", createUser)
	r.Get("/api/users/{id}", getUser)
	r.Put("/api/users/{id}", updateUser)
	r.Delete("/api/users/{id}", deleteUser)

	http.ListenAndServe(":8080", r)
}
