package com.petclinic.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class ArticleController {

    @GetMapping("/articles")
    public Object listArticles() { return null; }

    @PostMapping("/articles")
    public Object createArticle(@RequestBody Object body) { return null; }

    @GetMapping("/articles/{slug}")
    public Object getArticle(@PathVariable String slug) { return null; }

    @PutMapping("/articles/{slug}")
    public Object updateArticle(@PathVariable String slug, @RequestBody Object body) { return null; }

    @DeleteMapping("/articles/{slug}")
    public Object deleteArticle(@PathVariable String slug) { return null; }

    @GetMapping("/profiles/{username}")
    public Object getProfile(@PathVariable String username) { return null; }
}
