package com.ter.reco_backend.repository;

import com.ter.reco_backend.entity.Wishlist;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface WishlistRepository extends JpaRepository<Wishlist, String> {
    List<Wishlist> findByUserIdOrderByAddedAtDesc(String userId);
    Optional<Wishlist> findByUserIdAndItemId(String userId, String itemId);
    boolean existsByUserIdAndItemId(String userId, String itemId);
    void deleteByUserIdAndItemId(String userId, String itemId);
}