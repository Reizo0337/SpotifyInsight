export const MOCK_USER_PROFILE = {
  user_id: "mock_user_123",
  user_name: "Test User",
  stats: {
    total_tracks: 1540,
    top_genres: ["Rock", "Synthwave", "Cyberpunk", "Jazz"],
    hours_played: 245
  }
};

export const MOCK_STATS = {
  summary: "You've been listening to a lot of electronic music lately!",
  top_artists: [
    { name: "Perturbator", play_count: 150 },
    { name: "Carpenter Brut", play_count: 120 },
    { name: "The Midnight", play_count: 90 }
  ],
  energy_levels: { morning: 0.8, afternoon: 0.5, evening: 0.9 }
};

export const MOCK_TRACKS = [
  {
    spotify_id: "1",
    track_name: "Future Club",
    artist: "Perturbator",
    album: "Dangerous Days",
    popularity: 80,
    genre: "Synthwave",
    danceability: 0.7,
    energy: 0.9,
    tempo: 120,
    valence: 0.3
  },
  {
    spotify_id: "2",
    track_name: "Turbo Killer",
    artist: "Carpenter Brut",
    album: "Trilogy",
    popularity: 85,
    genre: "Synthwave",
    danceability: 0.6,
    energy: 0.95,
    tempo: 140,
    valence: 0.4
  },
  {
    spotify_id: "3",
    track_name: "Los Angeles",
    artist: "The Midnight",
    album: "Days of Thunder",
    popularity: 75,
    genre: "New Wave",
    danceability: 0.8,
    energy: 0.6,
    tempo: 105,
    valence: 0.9
  }
];

export const MOCK_SYNC_STATUS = {
  status: "success",
  new_tracks: 15,
  total_library: 1540,
  time_taken: "2.5s"
};
