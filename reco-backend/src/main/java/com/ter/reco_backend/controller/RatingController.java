package com.ter.reco_backend.controller;
 
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ter.reco_backend.entity.Item;
import com.ter.reco_backend.entity.Rating;
import com.ter.reco_backend.entity.User;
import com.ter.reco_backend.repository.ItemRepository;
import com.ter.reco_backend.repository.RatingRepository;
import com.ter.reco_backend.repository.UserRepository;

import lombok.RequiredArgsConstructor;
 
@RestController
@RequestMapping("/api/ratings")
@RequiredArgsConstructor
public class RatingController {
 
    private final RatingRepository ratingRepository;
    private final UserRepository userRepository;
    private final ItemRepository itemRepository;
 
    @PostMapping
    public ResponseEntity<?> addRating(@RequestBody Map<String, Object> body,
                                        Authentication auth) {
        String userId = auth.getName();
        String itemId = (String) body.get("itemId");
        float  score  = ((Number) body.get("score")).floatValue();
 
        if (ratingRepository.existsByUserIdAndItemId(userId, itemId))
            return ResponseEntity.badRequest().body(Map.of("error", "Déjà noté — utilisez PUT pour modifier"));
 
        User user = userRepository.findById(userId).orElseThrow();
        Item item = itemRepository.findById(itemId).orElseThrow();
 
        Rating rating = Rating.builder().user(user).item(item).score(score).build();
        ratingRepository.save(rating);
        return ResponseEntity.ok(rating);
    }
 
    @GetMapping("/me")
    public ResponseEntity<?> myRatings(Authentication auth) {
        return ResponseEntity.ok(ratingRepository.findByUserId(auth.getName()));
    }
 
    @PutMapping("/{id}")
    public ResponseEntity<?> updateRating(@PathVariable String id,
                                           @RequestBody Map<String, Object> body,
                                           Authentication auth) {
        return ratingRepository.findById(id)
                .filter(r -> r.getUser().getId().equals(auth.getName()))
                .map(r -> {
                    r.setScore(((Number) body.get("score")).floatValue());
                    return ResponseEntity.ok(ratingRepository.save(r));
                })
                .orElse(ResponseEntity.notFound().build());
    }
 
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteRating(@PathVariable String id, Authentication auth) {
        return ratingRepository.findById(id)
                .filter(r -> r.getUser().getId().equals(auth.getName()))
                .map(r -> {
                    ratingRepository.delete(r);
                    return ResponseEntity.ok(Map.of("message", "Note supprimée"));
                })
                .orElse(ResponseEntity.notFound().build());
    }
}