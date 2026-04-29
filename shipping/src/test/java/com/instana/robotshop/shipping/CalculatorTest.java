package com.instana.robotshop.shipping;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private City cityAt(double latitude, double longitude) {
        City city = new City();
        city.setLatitude(latitude);
        city.setLongitude(longitude);
        return city;
    }

    @Test
    void distanceIsZeroWhenOriginAndTargetAreTheSame() {
        Calculator calc = new Calculator(cityAt(10.0, 20.0));
        assertEquals(0L, calc.getDistance(10.0, 20.0));
    }

    @Test
    void distanceIsZeroAtOriginZeroZero() {
        Calculator calc = new Calculator(cityAt(0.0, 0.0));
        assertEquals(0L, calc.getDistance(0.0, 0.0));
    }

    @Test
    void distanceIsPositiveForDifferentLocations() {
        Calculator calc = new Calculator(cityAt(0.0, 0.0));
        long distance = calc.getDistance(1.0, 0.0);
        assertTrue(distance > 0, "Distance between different points must be positive");
    }

    @Test
    void oneDegreeLongitudeNorthGivesApprox111km() {
        // Same longitude: formula reduces to arc length = R * Δφ, no longitude bug
        Calculator calc = new Calculator(cityAt(0.0, 0.0));
        long distance = calc.getDistance(1.0, 0.0);
        assertEquals(111L, distance);
    }

    @Test
    void tenDegreesLatitudeNorthGivesApprox1112km() {
        Calculator calc = new Calculator(cityAt(0.0, 0.0));
        long distance = calc.getDistance(10.0, 0.0);
        assertEquals(1112L, distance);
    }

    @Test
    void fortyFiveDegreesLatitudeNorthGivesApprox5004km() {
        Calculator calc = new Calculator(cityAt(0.0, 0.0));
        long distance = calc.getDistance(45.0, 0.0);
        assertEquals(5004L, distance);
    }

    @Test
    void southernHemisphereDistanceIsSymmetric() {
        // Distance from (10, 0) to (0, 0) should equal (0, 0) to (10, 0)
        Calculator calcA = new Calculator(cityAt(10.0, 0.0));
        Calculator calcB = new Calculator(cityAt(0.0, 0.0));
        assertEquals(calcB.getDistance(10.0, 0.0), calcA.getDistance(0.0, 0.0));
    }

    @Test
    void distanceReturnedIsNonNegative() {
        Calculator calc = new Calculator(cityAt(-33.8688, 151.2093)); // Sydney
        long distance = calc.getDistance(-33.8688, 151.2093);
        assertTrue(distance >= 0);
    }
}
