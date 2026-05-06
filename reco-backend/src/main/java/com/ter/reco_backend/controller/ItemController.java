package com.ter.reco_backend.controller;
 
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.ter.reco_backend.entity.Item.ItemType;
import com.ter.reco_backend.repository.GenreRepository;
import com.ter.reco_backend.repository.ItemRepository;

import lombok.RequiredArgsConstructor;
 
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ItemController {
 
    private final ItemRepository itemRepository;
    private final GenreRepository genreRepository;
 
    @GetMapping("/items")
    public ResponseEntity<?> getItems(
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        var pageable = PageRequest.of(page, size);
        if (type != null) {
            return ResponseEntity.ok(itemRepository.findByType(ItemType.valueOf(type), pageable));
        }
        return ResponseEntity.ok(itemRepository.findAll(pageable));
    }
 
    @GetMapping("/items/{id}")
    public ResponseEntity<?> getItem(@PathVariable String id) {
        return itemRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
 
    @GetMapping("/items/search")
    public ResponseEntity<?> search(
            @RequestParam String q,
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        ItemType itemType = type != null ? ItemType.valueOf(type) : null;
        return ResponseEntity.ok(itemRepository.search(q, itemType, PageRequest.of(page, size)));
    }
 
    @GetMapping("/genres")
    public ResponseEntity<?> getGenres() {
        return ResponseEntity.ok(genreRepository.findAll());
    }
}