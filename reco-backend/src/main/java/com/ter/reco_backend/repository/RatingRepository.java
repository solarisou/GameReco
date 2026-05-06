package com.ter.reco_backend.repository;
 
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.ter.reco_backend.entity.Rating;
 
public interface RatingRepository extends JpaRepository<Rating, String> {
    List<Rating> findByUserId(String userId);
    Optional<Rating> findByUserIdAndItemId(String userId, String itemId);
    boolean existsByUserIdAndItemId(String userId, String itemId);
}