package com.ter.reco_backend.repository;
 
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.ter.reco_backend.entity.User;
 
public interface UserRepository extends JpaRepository<User, String> {
    Optional<User> findByEmail(String email);
    Optional<User> findByUsername(String username);
    boolean existsByEmail(String email);
    boolean existsByUsername(String username);
}