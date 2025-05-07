import { Box, Typography, Grid, Card, CardContent } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Club, Competition, Fixture } from '../types/api';

export default function Home() {
  const { data: recentFixtures } = useQuery<Fixture[]>({
    queryKey: ['recentFixtures'],
    queryFn: () => apiClient.get('/fixtures/recent').then(res => res.data),
  });

  const { data: topClubs } = useQuery<Club[]>({
    queryKey: ['topClubs'],
    queryFn: () => apiClient.get('/clubs/top').then(res => res.data),
  });

  const { data: activeCompetitions } = useQuery<Competition[]>({
    queryKey: ['activeCompetitions'],
    queryFn: () => apiClient.get('/competitions/active').then(res => res.data),
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome to Football Predictor
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Fixtures
              </Typography>
              {recentFixtures?.map((fixture) => (
                <Box key={fixture.id} sx={{ mb: 2 }}>
                  <Typography>
                    {fixture.home_team_id} vs {fixture.away_team_id}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(fixture.match_date).toLocaleDateString()}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Clubs
              </Typography>
              {topClubs?.map((club) => (
                <Box key={club.id} sx={{ mb: 2 }}>
                  <Typography>{club.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {club.country}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Competitions
              </Typography>
              <Grid container spacing={2}>
                {activeCompetitions?.map((competition) => (
                  <Grid item xs={12} sm={6} md={4} key={competition.id}>
                    <Box sx={{ p: 2, border: '1px solid #eee', borderRadius: 1 }}>
                      <Typography variant="subtitle1">{competition.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {competition.country}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
} 