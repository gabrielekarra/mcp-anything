package main

import (
	"net/http"

	"github.com/labstack/echo/v4"
)

type User struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

func listUsers(c echo.Context) error {
	return c.JSON(http.StatusOK, []User{})
}

func createUser(c echo.Context) error {
	return c.JSON(http.StatusCreated, User{ID: 1, Name: "Alice"})
}

func getUser(c echo.Context) error {
	id := c.Param("id")
	return c.JSON(http.StatusOK, User{ID: 1, Name: id})
}

func updateUser(c echo.Context) error {
	id := c.Param("id")
	return c.JSON(http.StatusOK, User{ID: 1, Name: id})
}

func deleteUser(c echo.Context) error {
	return c.JSON(http.StatusOK, map[string]bool{"deleted": true})
}

func healthCheck(c echo.Context) error {
	return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
}

func main() {
	e := echo.New()

	e.GET("/health", healthCheck)
	e.GET("/api/users", listUsers)
	e.POST("/api/users", createUser)
	e.GET("/api/users/:id", getUser)
	e.PUT("/api/users/:id", updateUser)
	e.DELETE("/api/users/:id", deleteUser)

	e.Logger.Fatal(e.Start(":8080"))
}
