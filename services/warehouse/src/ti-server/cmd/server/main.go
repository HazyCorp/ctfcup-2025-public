package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"ti-server/internal/handlers"
	"ti-server/internal/storage"
)

func main() {
	port := getEnv("PORT", "8080")
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "tiserver")
	dbPassword := getEnv("DB_PASSWORD", "tiserver")
	dbName := getEnv("DB_NAME", "tiserver")

	connString := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName,
	)

	logger := log.New(os.Stdout, "[TI-Server] ", log.LstdFlags)

	ctx := context.Background()
	var store *storage.Storage
	var err error

	logger.Println("Connecting to database...")
	for i := 0; i < 10; i++ {
		store, err = storage.NewStorage(ctx, connString)
		if err == nil {
			break
		}
		logger.Printf("Failed to connect to database (attempt %d/10): %v", i+1, err)
		time.Sleep(2 * time.Second)
	}

	if err != nil {
		logger.Fatalf("Could not connect to database after 10 attempts: %v", err)
	}
	defer store.Close()

	logger.Println("Connected to database successfully")

	cleanupCtx, cleanupCancel := context.WithCancel(context.Background())
	defer cleanupCancel()
	startCleanupWorker(cleanupCtx, store, logger)

	server := handlers.NewServer(store, logger)
	mux := http.NewServeMux()

	mux.HandleFunc("/feeds", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			server.HandleGetFeeds(w, r)
		} else if r.Method == http.MethodPost {
			server.HandleCreateFeed(w, r)
		} else {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/feeds/", func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, "/feeds/")

		if strings.Contains(path, "/iocs") {
			if r.Method == http.MethodPost {
				server.HandleAddIOC(w, r)
			} else if r.Method == http.MethodGet {
				server.HandleGetIOCs(w, r)
			} else {
				http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			}
		} else {
			if r.Method == http.MethodGet {
				server.HandleGetFeed(w, r)
			} else {
				http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			}
		}
	})

	fs := http.FileServer(http.Dir("./static"))
	mux.Handle("/assets/", fs)
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if !strings.HasPrefix(r.URL.Path, "/feeds") && !strings.HasPrefix(r.URL.Path, "/indicators") && !strings.HasPrefix(r.URL.Path, "/assets") {
			http.ServeFile(w, r, "./static/index.html")
		} else {
			fs.ServeHTTP(w, r)
		}
	})

	httpServer := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		logger.Printf("Starting TI Server on port %s", port)
		if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Fatalf("Server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	cleanupCancel()
	logger.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(ctx); err != nil {
		logger.Fatalf("Server forced to shutdown: %v", err)
	}

	logger.Println("Server stopped")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func startCleanupWorker(ctx context.Context, store *storage.Storage, logger *log.Logger) {
	ticker := time.NewTicker(5 * time.Minute)

	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				if err := store.CleanExpiredData(context.Background(), time.Hour); err != nil {
					logger.Printf("Failed to clean expired TI data: %v", err)
				}
			case <-ctx.Done():
				return
			}
		}
	}()
}
