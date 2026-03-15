package main

import (
	"github.com/gin-gonic/gin"
)

func healthCheck(c *gin.Context) {
	c.JSON(200, gin.H{"status": "ok"})
}

func listUsers(c *gin.Context) {
	limit := c.Query("limit")
	offset := c.DefaultQuery("offset", "0")
	c.JSON(200, gin.H{"limit": limit, "offset": offset})
}

func getUser(c *gin.Context) {
	id := c.Param("id")
	c.JSON(200, gin.H{"id": id})
}

func createUser(c *gin.Context) {
	var body map[string]interface{}
	c.BindJSON(&body)
	c.JSON(201, body)
}

func updateUser(c *gin.Context) {
	id := c.Param("id")
	var body map[string]interface{}
	c.ShouldBindJSON(&body)
	c.JSON(200, gin.H{"id": id})
}

func deleteUser(c *gin.Context) {
	id := c.Param("id")
	c.JSON(200, gin.H{"deleted": id})
}
