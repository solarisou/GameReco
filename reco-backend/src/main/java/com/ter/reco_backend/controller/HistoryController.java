package com.ter.reco_backend.controller;
 
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ter.reco_backend.entity.History;
import com.ter.reco_backend.entity.Item;
import com.ter.reco_backend.entity.User;
import com.ter.reco_backend.repository.HistoryRepository;
import com.ter.reco_backend.repository.ItemRepository;
import com.ter.reco_backend.repository.UserRepository;

import lombok.RequiredArgsConstructor;
 
@RestController
@RequestMapping("/api/history")
@RequiredArgsConstructor
public class HistoryController {
 
    private final HistoryRepository historyRepository;
    private final UserRepository userRepository;
    private final ItemRepository itemRepository;
 
    @PostMapping
    public ResponseEntity<?> addHistory(@RequestBody Map<String, String> body,
                                         Authentication auth) {
        User user = userRepository.findById(auth.getName()).orElseThrow();
        Item item = itemRepository.findById(body.get("itemId")).orElseThrow();
        History h = History.builder().user(user).item(item).build();
        historyRepository.save(h);
        return ResponseEntity.ok(h);
    }
 
    @GetMapping("/me")
    public ResponseEntity<?> myHistory(Authentication auth) {
        return ResponseEntity.ok(historyRepository.findByUserIdOrderByViewedAtDesc(auth.getName()));
    }
}