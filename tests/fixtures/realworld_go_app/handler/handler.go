package handler

import (
	"github.com/gin-gonic/gin"
)

func RegisterRoutes(r *gin.Engine) {
	api := r.Group("/api")
	{
		api.GET("/articles", ListArticles)
		api.POST("/articles", CreateArticle)
		api.GET("/articles/:slug", GetArticle)
		api.PUT("/articles/:slug", UpdateArticle)
		api.DELETE("/articles/:slug", DeleteArticle)
		api.GET("/profiles/:username", GetProfile)
		api.POST("/users/login", Login)
		api.POST("/users", Register)
	}
}

func ListArticles(c *gin.Context)  {}
func CreateArticle(c *gin.Context) {}
func GetArticle(c *gin.Context)    {}
func UpdateArticle(c *gin.Context) {}
func DeleteArticle(c *gin.Context) {}
func GetProfile(c *gin.Context)    {}
func Login(c *gin.Context)         {}
func Register(c *gin.Context)      {}
