package com.example.web;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    @GetMapping
    public List<Product> listProducts(@RequestParam(required = false) String category) {
        return List.of();
    }

    @GetMapping("/{id}")
    public Product getProduct(@PathVariable Long id) {
        return new Product();
    }

    @PostMapping
    public Product createProduct(@RequestBody Map<String, Object> data) {
        return new Product();
    }

    @DeleteMapping("/{id}")
    public void deleteProduct(@PathVariable Long id) {
    }
}
