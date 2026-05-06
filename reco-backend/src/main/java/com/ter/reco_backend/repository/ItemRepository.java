package com.ter.reco_backend.repository;
 
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.ter.reco_backend.entity.Item;
import com.ter.reco_backend.entity.Item.ItemType;
 
public interface ItemRepository extends JpaRepository<Item, String> {
    Page<Item> findByType(ItemType type, Pageable pageable);
 
    @Query("SELECT i FROM Item i WHERE " +
           "(:type IS NULL OR i.type = :type) AND " +
           "LOWER(i.title) LIKE LOWER(CONCAT('%', :q, '%'))")
    Page<Item> search(@Param("q") String q,
                      @Param("type") ItemType type,
                      Pageable pageable);
}