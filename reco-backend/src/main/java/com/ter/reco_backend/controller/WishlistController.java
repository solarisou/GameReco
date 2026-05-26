package com.ter.reco_backend.controller;

import com.ter.reco_backend.dto.WishlistDto;
import com.ter.reco_backend.entity.Item;
import com.ter.reco_backend.entity.User;
import com.ter.reco_backend.entity.Wishlist;
import com.ter.reco_backend.repository.ItemRepository;
import com.ter.reco_backend.repository.UserRepository;
import com.ter.reco_backend.repository.WishlistRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/wishlist")
@RequiredArgsConstructor
public class WishlistController {

    private final WishlistRepository wishlistRepository;
    private final UserRepository     userRepository;
    private final ItemRepository     itemRepository;

    // ── GET /api/wishlist/me ──────────────────────────────
    @GetMapping("/me")
    public ResponseEntity<?> getMyWishlist(Authentication auth) {
        List<WishlistDto> result = wishlistRepository
                .findByUserIdOrderByAddedAtDesc(auth.getName())
                .stream()
                .map(WishlistDto::from)
                .collect(Collectors.toList());
        return ResponseEntity.ok(result);
    }

    // ── POST /api/wishlist ────────────────────────────────
    @PostMapping
    public ResponseEntity<?> addToWishlist(@RequestBody Map<String, String> body,
                                            Authentication auth) {
        String userId = auth.getName();
        String itemId = body.get("itemId");

        if (wishlistRepository.existsByUserIdAndItemId(userId, itemId)) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Item déjà dans la wishlist"));
        }

        User user = userRepository.findById(userId).orElseThrow();
        Item item = itemRepository.findById(itemId).orElseThrow();

        Wishlist entry = Wishlist.builder().user(user).item(item).build();
        wishlistRepository.save(entry);
        return ResponseEntity.ok(Map.of("message", "Ajouté à la wishlist", "itemId", itemId));
    }

    // ── DELETE /api/wishlist/{itemId} ─────────────────────
    @DeleteMapping("/{itemId}")
    @Transactional
    public ResponseEntity<?> removeFromWishlist(@PathVariable String itemId,
                                                 Authentication auth) {
        String userId = auth.getName();
        if (!wishlistRepository.existsByUserIdAndItemId(userId, itemId)) {
            return ResponseEntity.notFound().build();
        }
        wishlistRepository.deleteByUserIdAndItemId(userId, itemId);
        return ResponseEntity.ok(Map.of("message", "Retiré de la wishlist", "itemId", itemId));
    }

    // ── GET /api/wishlist/check/{itemId} ──────────────────
    @GetMapping("/check/{itemId}")
    public ResponseEntity<?> checkWishlist(@PathVariable String itemId,
                                            Authentication auth) {
        boolean inWishlist = wishlistRepository
                .existsByUserIdAndItemId(auth.getName(), itemId);
        return ResponseEntity.ok(Map.of("inWishlist", inWishlist));
    }
}