package com.instana.robotshop.shipping;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CartHelperTest {

    @Test
    void constructorCreatesInstance() {
        CartHelper helper = new CartHelper("http://cart:8080/cart/");
        assertNotNull(helper);
    }

    @Test
    void addToCartReturnsEmptyStringWhenConnectionRefused() {
        // Port 1 is reserved and will be refused immediately — no slow timeout
        CartHelper helper = new CartHelper("http://localhost:1/cart/");
        String result = helper.addToCart("order-123", "{\"cost\":5.0,\"location\":\"Test City\",\"distance\":100}");
        assertEquals("", result);
    }

    @Test
    void addToCartReturnsEmptyStringForMalformedBaseUrl() {
        // Invalid URI causes an exception caught internally, returning empty string
        CartHelper helper = new CartHelper("not-a-valid-url/");
        String result = helper.addToCart("id", "{}");
        assertEquals("", result);
    }

    @Test
    void addToCartReturnsEmptyStringForUnreachableHost() {
        CartHelper helper = new CartHelper("http://no-such-host-xyzabc.local/cart/");
        String result = helper.addToCart("id", "{}");
        assertEquals("", result);
    }
}
