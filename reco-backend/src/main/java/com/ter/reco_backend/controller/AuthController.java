package com.ter.reco_backend.controller;
 
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ter.reco_backend.entity.User;
import com.ter.reco_backend.repository.UserRepository;
import com.ter.reco_backend.security.JwtUtil;

import lombok.RequiredArgsConstructor;
 
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {
 
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
 
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String email    = body.get("email");
        String password = body.get("password");
 
        if (userRepository.existsByEmail(email))
            return ResponseEntity.badRequest().body(Map.of("error", "Email déjà utilisé"));
        if (userRepository.existsByUsername(username))
            return ResponseEntity.badRequest().body(Map.of("error", "Username déjà pris"));
 
        User user = User.builder()
                .username(username)
                .email(email)
                .passwordHash(passwordEncoder.encode(password))
                .build();
        userRepository.save(user);
        return ResponseEntity.ok(Map.of("message", "Compte créé", "userId", user.getId()));
    }
 
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> body) {
        String email    = body.get("email");
        String password = body.get("password");
 
        return userRepository.findByEmail(email)
                .filter(u -> passwordEncoder.matches(password, u.getPasswordHash()))
                .map(u -> ResponseEntity.ok(Map.of("token", jwtUtil.generateToken(u.getId()))))
                .orElse(ResponseEntity.status(401).body(Map.of("error", "Identifiants invalides")));
    }
}