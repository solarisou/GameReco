package com.ter.reco_backend.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;

import java.time.LocalDateTime;

@Entity
@Table(name = "wishlist",
    uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "item_id"}))
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Wishlist {

    @Id
    @UuidGenerator
    @Column(length = 36)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "item_id", nullable = false)
    private Item item;

    @Column(name = "added_at", nullable = false, updatable = false)
    private LocalDateTime addedAt;

    @PrePersist
    public void prePersist() {
        this.addedAt = LocalDateTime.now();
    }
}