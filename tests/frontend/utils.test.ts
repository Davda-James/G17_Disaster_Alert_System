/**
 * Frontend Tests - Utility Functions
 * Tests common utility functions and helpers
 */

import { describe, it, expect } from "vitest";

describe("Utility Functions", () => {
  // =========================================================================
  // FE-009: Email Validation
  // =========================================================================
  describe("Email Validation", () => {
    const isValidEmail = (email: string): boolean => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    };

    it("FE-009a: should validate correct email formats", () => {
      expect(isValidEmail("user@example.com")).toBe(true);
      expect(isValidEmail("user.name@domain.co.uk")).toBe(true);
      expect(isValidEmail("user+tag@example.com")).toBe(true);
    });

    it("FE-009b: should reject invalid email formats", () => {
      expect(isValidEmail("")).toBe(false);
      expect(isValidEmail("invalid")).toBe(false);
      expect(isValidEmail("@example.com")).toBe(false);
      expect(isValidEmail("user@")).toBe(false);
    });
  });

  // =========================================================================
  // FE-010: Phone Validation
  // =========================================================================
  describe("Phone Validation", () => {
    const isValidPhone = (phone: string): boolean => {
      const phoneRegex = /^\+?[1-9]\d{9,14}$/;
      return phoneRegex.test(phone.replace(/[\s-]/g, ""));
    };

    it("FE-010a: should validate correct phone formats", () => {
      expect(isValidPhone("+919876543210")).toBe(true);
      expect(isValidPhone("9876543210")).toBe(true);
      expect(isValidPhone("+1234567890")).toBe(true);
    });

    it("FE-010b: should reject invalid phone formats", () => {
      expect(isValidPhone("")).toBe(false);
      expect(isValidPhone("123")).toBe(false);
    });
  });

  // =========================================================================
  // FE-011: Alert Type Formatting
  // =========================================================================
  describe("Alert Type Formatting", () => {
    const formatAlertType = (type: string): string => {
      const typeMap: Record<string, string> = {
        flood: "🌊 Flood",
        earthquake: "🏚️ Earthquake",
        cyclone: "🌀 Cyclone",
        tsunami: "🌊 Tsunami",
        fire: "🔥 Fire",
        landslide: "⛰️ Landslide",
        drought: "☀️ Drought",
      };
      return typeMap[type.toLowerCase()] || type;
    };

    it("FE-011: should format alert types with emojis", () => {
      expect(formatAlertType("flood")).toBe("🌊 Flood");
      expect(formatAlertType("earthquake")).toBe("🏚️ Earthquake");
      expect(formatAlertType("cyclone")).toBe("🌀 Cyclone");
      expect(formatAlertType("unknown")).toBe("unknown");
    });
  });

  // =========================================================================
  // FE-012: Severity Color Mapping
  // =========================================================================
  describe("Severity Color Mapping", () => {
    const getSeverityColor = (severity: string): string => {
      const colorMap: Record<string, string> = {
        low: "green",
        medium: "yellow",
        high: "orange",
        critical: "red",
      };
      return colorMap[severity.toLowerCase()] || "gray";
    };

    it("FE-012: should map severity to correct colors", () => {
      expect(getSeverityColor("low")).toBe("green");
      expect(getSeverityColor("medium")).toBe("yellow");
      expect(getSeverityColor("high")).toBe("orange");
      expect(getSeverityColor("critical")).toBe("red");
      expect(getSeverityColor("unknown")).toBe("gray");
    });
  });

  // =========================================================================
  // FE-013: Distance Calculation
  // =========================================================================
  describe("Distance Calculation", () => {
    const calculateDistance = (
      lat1: number,
      lng1: number,
      lat2: number,
      lng2: number
    ): number => {
      const R = 6371; // Earth's radius in km
      const dLat = ((lat2 - lat1) * Math.PI) / 180;
      const dLng = ((lng2 - lng1) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
          Math.cos((lat2 * Math.PI) / 180) *
          Math.sin(dLng / 2) *
          Math.sin(dLng / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    };

    it("FE-013a: should calculate zero distance for same point", () => {
      const distance = calculateDistance(19.076, 72.877, 19.076, 72.877);
      expect(distance).toBe(0);
    });

    it("FE-013b: should calculate Mumbai to Delhi distance (~1200km)", () => {
      const distance = calculateDistance(19.076, 72.877, 28.613, 77.209);
      expect(distance).toBeGreaterThan(1100);
      expect(distance).toBeLessThan(1300);
    });

    it("FE-013c: should calculate Mumbai to Pune distance (~120km)", () => {
      const distance = calculateDistance(19.076, 72.877, 18.52, 73.856);
      expect(distance).toBeGreaterThan(100);
      expect(distance).toBeLessThan(150);
    });
  });

  // =========================================================================
  // FE-014: Time Formatting
  // =========================================================================
  describe("Time Formatting", () => {
    const formatTimeAgo = (timestamp: string): string => {
      const now = new Date();
      const date = new Date(timestamp);
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins} min ago`;
      if (diffHours < 24) return `${diffHours} hours ago`;
      return `${diffDays} days ago`;
    };

    it("FE-014: should format recent timestamps correctly", () => {
      const now = new Date().toISOString();
      expect(formatTimeAgo(now)).toBe("Just now");
    });
  });

  // =========================================================================
  // FE-015: Indian States List
  // =========================================================================
  describe("Indian States Data", () => {
    const indianStates = [
      "Andhra Pradesh",
      "Arunachal Pradesh",
      "Assam",
      "Bihar",
      "Chhattisgarh",
      "Goa",
      "Gujarat",
      "Haryana",
      "Himachal Pradesh",
      "Jharkhand",
      "Karnataka",
      "Kerala",
      "Madhya Pradesh",
      "Maharashtra",
      "Manipur",
      "Meghalaya",
      "Mizoram",
      "Nagaland",
      "Odisha",
      "Punjab",
      "Rajasthan",
      "Sikkim",
      "Tamil Nadu",
      "Telangana",
      "Tripura",
      "Uttar Pradesh",
      "Uttarakhand",
      "West Bengal",
      "Delhi",
    ];

    it("FE-015: should have correct number of states", () => {
      expect(indianStates.length).toBeGreaterThanOrEqual(28);
    });

    it("FE-015b: should include major states", () => {
      expect(indianStates).toContain("Maharashtra");
      expect(indianStates).toContain("Delhi");
      expect(indianStates).toContain("Tamil Nadu");
      expect(indianStates).toContain("Karnataka");
    });
  });
});
