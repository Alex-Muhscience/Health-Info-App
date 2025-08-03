/**
 * Service Worker for Health Management System PWA
 * Provides offline functionality, push notifications, and caching
 */

const CACHE_NAME = 'hms-pwa-v1.0.0';
const STATIC_CACHE = 'hms-static-v1.0.0';
const DYNAMIC_CACHE = 'hms-dynamic-v1.0.0';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/static/css/bootstrap.min.css',
    '/static/css/style.css',
    '/static/js/jquery.min.js',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/app.js',
    '/static/js/dashboard.js',
    '/static/images/logo.png',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-512x512.png',
    '/auth/login/',
    '/dashboard/',
    '/offline/'
];

// API endpoints to cache responses
const API_CACHE_PATTERNS = [
    '/api/dashboard/stats',
    '/api/clients',
    '/api/appointments',
    '/api/staff'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('HMS Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Failed to cache static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('HMS Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && 
                            cacheName !== DYNAMIC_CACHE &&
                            cacheName !== CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('HMS Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve cached content and implement caching strategies
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests with appropriate strategies
    if (STATIC_ASSETS.some(asset => url.pathname.includes(asset))) {
        // Cache First strategy for static assets
        event.respondWith(handleStaticAssets(request));
    } else if (url.pathname.startsWith('/api/')) {
        // Network First strategy for API calls
        event.respondWith(handleAPIRequests(request));
    } else if (url.pathname.startsWith('/auth/') || 
               url.pathname.startsWith('/dashboard/') ||
               url.pathname.startsWith('/clients/')) {
        // Stale While Revalidate for pages
        event.respondWith(handlePageRequests(request));
    } else {
        // Default network first
        event.respondWith(handleDefaultRequests(request));
    }
});

// Cache First strategy for static assets
async function handleStaticAssets(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        const cache = await caches.open(STATIC_CACHE);
        cache.put(request, networkResponse.clone());
        return networkResponse;
    } catch (error) {
        console.error('Static asset fetch failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network First strategy for API requests
async function handleAPIRequests(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, checking cache for API request');
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Add offline indicator to response
            const responseBody = await cachedResponse.text();
            const offlineResponse = new Response(responseBody, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: {
                    ...cachedResponse.headers,
                    'X-Served-By': 'sw-cache',
                    'X-Offline': 'true'
                }
            });
            return offlineResponse;
        }
        
        // Return offline fallback
        return new Response(JSON.stringify({
            error: 'Network unavailable',
            offline: true,
            message: 'This data is not available offline'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Stale While Revalidate for page requests
async function handlePageRequests(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request)
        .then(networkResponse => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
            }
            return networkResponse;
        })
        .catch(() => {
            // Return offline page if no cached version
            return caches.match('/offline/');
        });
    
    return cachedResponse || fetchPromise;
}

// Default Network First strategy
async function handleDefaultRequests(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        return cachedResponse || caches.match('/offline/');
    }
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('Push notification received');
    
    let notificationData = {
        title: 'HMS Notification',
        body: 'You have a new notification',
        icon: '/static/images/icons/icon-192x192.png',
        badge: '/static/images/icons/badge-72x72.png',
        tag: 'hms-notification',
        requireInteraction: true,
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/images/icons/view-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/images/icons/dismiss-icon.png'
            }
        ]
    };
    
    if (event.data) {
        try {
            const data = event.data.json();
            notificationData = { ...notificationData, ...data };
        } catch (error) {
            console.error('Error parsing push data:', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    const action = event.action;
    const notification = event.notification;
    
    if (action === 'view') {
        // Open the app
        event.waitUntil(
            clients.openWindow('/dashboard/')
        );
    } else if (action === 'dismiss') {
        // Just close the notification
        console.log('Notification dismissed');
    } else {
        // Default action - open app
        event.waitUntil(
            clients.openWindow('/dashboard/')
        );
    }
});

// Background sync for offline data submission
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync-appointments') {
        event.waitUntil(syncOfflineAppointments());
    } else if (event.tag === 'background-sync-visits') {
        event.waitUntil(syncOfflineVisits());
    }
});

// Sync offline appointments when connection is restored
async function syncOfflineAppointments() {
    try {
        const offlineData = await getOfflineData('appointments');
        
        for (const appointment of offlineData) {
            try {
                const response = await fetch('/api/appointments', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': appointment.token
                    },
                    body: JSON.stringify(appointment.data)
                });
                
                if (response.ok) {
                    await removeOfflineData('appointments', appointment.id);
                    console.log('Synced offline appointment:', appointment.id);
                }
            } catch (error) {
                console.error('Failed to sync appointment:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Sync offline visits when connection is restored
async function syncOfflineVisits() {
    try {
        const offlineData = await getOfflineData('visits');
        
        for (const visit of offlineData) {
            try {
                const response = await fetch('/api/visits', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': visit.token
                    },
                    body: JSON.stringify(visit.data)
                });
                
                if (response.ok) {
                    await removeOfflineData('visits', visit.id);
                    console.log('Synced offline visit:', visit.id);
                }
            } catch (error) {
                console.error('Failed to sync visit:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Helper functions for offline data management
async function getOfflineData(type) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const request = new Request(`/offline-data/${type}`);
    const response = await cache.match(request);
    
    if (response) {
        return await response.json();
    }
    return [];
}

async function removeOfflineData(type, id) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const request = new Request(`/offline-data/${type}/${id}`);
    await cache.delete(request);
}
