package com.ter.reco_backend.repository;
 
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.ter.reco_backend.entity.Item.ItemType;
import com.ter.reco_backend.entity.Recommendation;
 
public interface RecommendationRepository extends JpaRepository<Recommendation, String> {
 
    List<Recommendation> findByUserIdOrderByScoreDesc(String userId);
 
    @Query("SELECT r FROM Recommendation r WHERE r.user.id = :userId " +
           "AND (:type IS NULL OR r.item.type = :type) " +
           "ORDER BY r.score DESC")
    List<Recommendation> findByUserIdAndType(@Param("userId") String userId,
                                              @Param("type") ItemType type);
}