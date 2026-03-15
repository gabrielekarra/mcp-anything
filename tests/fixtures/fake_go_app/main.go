package main

import (
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	r.GET("/health", healthCheck)

	v1 := r.Group("/api/v1")
	{
		v1.GET("/users", listUsers)
		v1.GET("/users/:id", getUser)
		v1.POST("/users", createUser)
		v1.PUT("/users/:id", updateUser)
		v1.DELETE("/users/:id", deleteUser)
	}

	r.Run(":8080")
}
