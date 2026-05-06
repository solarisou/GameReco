package com.ter.reco_backend.controller;
 
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ter.reco_backend.repository.UserRepository;

import lombok.RequiredArgsConstructor;
 
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
 
    private final UserRepository userRepository;
 
    @GetMapping("/me")
    public ResponseEntity<?> me(Authentication auth) {
        return userRepository.findById(auth.getName())
                .map(u -> ResponseEntity.ok(Map.of(
                        "id", u.getId(),
                        "username", u.getUsername(),
                        "email", u.getEmail(),
                        "createdAt", u.getCreatedAt()
                )))
                .orElse(ResponseEntity.notFound().build());
    }
 
    @PutMapping("/me")
    public ResponseEntity<?> updateMe(@RequestBody Map<String, String> body,
                                       Authentication auth) {
        return userRepository.findById(auth.getName())
                .map(u -> {
                    if (body.containsKey("username")) u.setUsername(body.get("username"));
                    if (body.containsKey("email"))    u.setEmail(body.get("email"));
                    return ResponseEntity.ok(userRepository.save(u));
                })
                .orElse(ResponseEntity.notFound().build());
    }
}