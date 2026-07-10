import { useEffect, useMemo, useState } from 'react';
import './App.css';
import AccidentHeatmap from './components/AccidentHeatmap';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const STATE_ALL = '__ALL__';

function App() {
  // Data loading status
  const [isDataReady, setIsDataReady] = useState(false);
  const [loadingError, setLoadingError] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState('Initializing...');

  const [leaderboardItems, setLeaderboardItems] = useState([]);
  const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(true);
  const [leaderboardError, setLeaderboardError] = useState(null);
  const [selectedState, setSelectedState] = useState(STATE_ALL);
  const [topLimit, setTopLimit] = useState(10);
  const [mapSunFilter, setMapSunFilter] = useState('ALL');
  const [mapSeverityMin, setMapSeverityMin] = useState(1);
  const [mapSeverityMax, setMapSeverityMax] = useState(4);
  const [weatherBreakdown, setWeatherBreakdown] = useState([]);
  const [isLoadingWeather, setIsLoadingWeather] = useState(true);
  const [weatherError, setWeatherError] = useState(null);
  const [timeSeries, setTimeSeries] = useState([]);
  const [isLoadingTimeSeries, setIsLoadingTimeSeries] = useState(true);
  const [timeSeriesError, setTimeSeriesError] = useState(null);
  const [timeSeriesView, setTimeSeriesView] = useState('annual'); // 'annual' or 'monthly'
  const [selectedYear, setSelectedYear] = useState(2023);
  const [monthlyTimeSeries, setMonthlyTimeSeries] = useState([]);
  const [isLoadingMonthly, setIsLoadingMonthly] = useState(false);
  const [mapPoints, setMapPoints] = useState([]);
  const [isLoadingMap, setIsLoadingMap] = useState(true);
  const [mapError, setMapError] = useState(null);
  
  // Separate data for severity distribution (no filters)
  const [allMapPoints, setAllMapPoints] = useState([]);
  const [isLoadingAllMapPoints, setIsLoadingAllMapPoints] = useState(true);
  
  // Separate data for weather pie chart (only sun filter)
  const [weatherPieSunFilter, setWeatherPieSunFilter] = useState('ALL');
  const [weatherPiePoints, setWeatherPiePoints] = useState([]);
  const [isLoadingWeatherPie, setIsLoadingWeatherPie] = useState(true);
  
  const [severityGraphFilter, setSeverityGraphFilter] = useState('ALL');
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [hoveredWeather, setHoveredWeather] = useState(null);
  const [weatherDistribution, setWeatherDistribution] = useState([]);
  const [isLoadingWeatherDist, setIsLoadingWeatherDist] = useState(true);
  const [weatherDistError, setWeatherDistError] = useState(null);
  const [hoveredDistBar, setHoveredDistBar] = useState(null);
  const [selectedWeatherMetric, setSelectedWeatherMetric] = useState('temperature');

  // Check if data is ready on component mount and poll until ready
  useEffect(() => {
    const checkDataStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();
        
        if (data.ready) {
          setIsDataReady(true);
          setLoadingError(null);
        } else {
          setLoadingProgress(data.error || 'Loading datasets...');
          // Poll again after 1 second
          setTimeout(checkDataStatus, 1000);
        }
      } catch (error) {
        setLoadingError('Failed to connect to server. Please ensure the backend is running.');
        console.error('Error checking data status:', error);
        // Retry after 2 seconds
        setTimeout(checkDataStatus, 2000);
      }
    };

    checkDataStatus();
  }, []);

  const numberFormatter = useMemo(
    () =>
      new Intl.NumberFormat('en-US', {
        notation: 'compact',
        compactDisplay: 'short',
      }),
    []
  );

  const percentFormatter = useMemo(
    () =>
      new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      }),
    []
  );

  const availableStates = useMemo(() => {
    const stateSet = new Set(mapPoints.map((p) => p.state));
    return Array.from(stateSet).sort();
  }, [mapPoints]);

  const mapStats = useMemo(() => {
    if (!mapPoints.length) {
      return { totalAccidents: 0, avgSeverity: 0, totalCities: 0 };
    }
    const total = mapPoints.reduce((sum, p) => sum + p.total_accidents, 0);
    const weightedSeverity = mapPoints.reduce(
      (sum, p) => sum + p.avg_severity * p.total_accidents,
      0
    );
    return {
      totalAccidents: total,
      avgSeverity: total > 0 ? weightedSeverity / total : 0,
      totalCities: mapPoints.length,
    };
  }, [mapPoints]);

  const severityDistribution = useMemo(() => {
    const counts = { 1: 0, 2: 0, 3: 0, 4: 0 };
    allMapPoints.forEach((point) => {
      const sev = Math.round(point.avg_severity);
      if (sev >= 1 && sev <= 4) {
        counts[sev] += point.total_accidents;
      }
    });
    const total = Object.values(counts).reduce((sum, val) => sum + val, 0);
    return Object.entries(counts).map(([severity, count]) => ({
      severity: Number(severity),
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
    }));
  }, [allMapPoints]);

  const weatherConditionsComparison = useMemo(() => {
    const weatherCounts = {};
    weatherPiePoints.forEach((point) => {
      const weather = point.most_common_weather || 'Unknown';
      if (!weatherCounts[weather]) {
        weatherCounts[weather] = 0;
      }
      weatherCounts[weather] += point.total_accidents;
    });
    const total = Object.values(weatherCounts).reduce((sum, val) => sum + val, 0);
    
    // Use a fixed set of highly distinct colors - assign in order
    const distinctColors = [
      '#facc15', // Bright Yellow
      '#3b82f6', // Bright Blue
      '#ef4444', // Bright Red
      '#10b981', // Bright Green
      '#f97316', // Bright Orange
      '#8b5cf6', // Bright Purple
      '#06b6d4', // Cyan
      '#ec4899', // Pink
      '#84cc16', // Lime
      '#f59e0b', // Amber
    ];
    
    // Calculate percentages based on total first, then sort
    const allItems = Object.entries(weatherCounts)
      .map(([weather, count]) => ({
        label: weather,
        count,
        percentage: total > 0 ? (count / total) * 100 : 0,
      }))
      .sort((a, b) => b.count - a.count);
    
    // Take top items that cover at least 95% of data, or top 6, whichever is more
    let cumulativePercentage = 0;
    let itemsToShow = [];
    for (let i = 0; i < allItems.length && (cumulativePercentage < 95 || i < 6); i++) {
      itemsToShow.push(allItems[i]);
      cumulativePercentage += allItems[i].percentage;
    }
    
    // If we don't have 100%, add "Other" category
    if (cumulativePercentage < 99.9 && itemsToShow.length < allItems.length) {
      const otherCount = allItems.slice(itemsToShow.length).reduce((sum, item) => sum + item.count, 0);
      itemsToShow.push({
        label: 'Other',
        count: otherCount,
        percentage: 100 - cumulativePercentage,
      });
    }
    
    // Assign distinct colors in order
    return itemsToShow.map((item, index) => ({
      ...item,
      color: distinctColors[index % distinctColors.length],
    }));
  }, [weatherPiePoints]);

  const topStatesChart = useMemo(() => {
    const stateCounts = {};
    mapPoints.forEach((point) => {
      if (!stateCounts[point.state]) {
        stateCounts[point.state] = 0;
      }
      stateCounts[point.state] += point.total_accidents;
    });
    return Object.entries(stateCounts)
      .map(([state, count]) => ({ state, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [mapPoints]);

  useEffect(() => {
    if (selectedState !== STATE_ALL && !availableStates.includes(selectedState)) {
      setSelectedState(STATE_ALL);
    }
  }, [availableStates, selectedState]);

  useEffect(() => {
    const controller = new AbortController();
    const fetchLeaderboard = async () => {
      setIsLoadingLeaderboard(true);
      try {
        const endpoint =
          selectedState === STATE_ALL
            ? `${API_BASE_URL}/analytics/top-states?limit=${topLimit}`
            : `${API_BASE_URL}/analytics/top-cities?state=${selectedState}&limit=${topLimit}`;
        const response = await fetch(endpoint, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        const transformed =
          selectedState === STATE_ALL
            ? (payload.items ?? []).map((item) => ({
                id: item.State,
                label: item.State,
                metric: item.total_accidents,
                description: item.avg_distance
                  ? `Avg distance: ${item.avg_distance.toFixed(2)} mi`
                  : undefined,
              }))
            : (payload.items ?? []).map((item) => ({
                id: `${item.city}-${item.state}`,
                label: `${item.city}, ${item.state}`,
                metric: item.total_accidents,
                description: `Avg severity ${item.avg_severity}`,
              }));

        setLeaderboardItems(transformed);
        setLeaderboardError(null);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch leaderboard data', error);
        setLeaderboardItems([]);
        setLeaderboardError('Unable to load leaderboard right now.');
      } finally {
        setIsLoadingLeaderboard(false);
      }
    };

    fetchLeaderboard();

    return () => controller.abort();
  }, [selectedState, topLimit]);

  // Optimized: Fetch initial data in parallel for faster dashboard load
  useEffect(() => {
    const controller = new AbortController();
    
    const fetchInitialData = async () => {
      // Fetch all initial data in parallel (excluding weather distribution which depends on selectedWeatherMetric)
      const [weatherResponse, timeSeriesResponse] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/analytics/weather-breakdown`, { signal: controller.signal }),
        fetch(`${API_BASE_URL}/analytics/time-series`, { signal: controller.signal }),
      ]);

      // Handle weather breakdown
      setIsLoadingWeather(true);
      if (weatherResponse.status === 'fulfilled' && weatherResponse.value.ok) {
        try {
          const payload = await weatherResponse.value.json();
          setWeatherBreakdown(payload.items ?? []);
          setWeatherError(null);
        } catch (error) {
          console.error('Failed to parse weather breakdown', error);
          setWeatherBreakdown([]);
          setWeatherError('Unable to load weather breakdown right now.');
        }
      } else {
        setWeatherBreakdown([]);
        setWeatherError('Unable to load weather breakdown right now.');
      }
      setIsLoadingWeather(false);

      // Handle time series
      setIsLoadingTimeSeries(true);
      if (timeSeriesResponse.status === 'fulfilled' && timeSeriesResponse.value.ok) {
        try {
          const payload = await timeSeriesResponse.value.json();
          setTimeSeries(payload.items ?? []);
          setTimeSeriesError(null);
        } catch (error) {
          console.error('Failed to parse time series data', error);
          setTimeSeries([]);
          setTimeSeriesError('Unable to load time series data right now.');
        }
      } else {
        setTimeSeries([]);
        setTimeSeriesError('Unable to load time series data right now.');
      }
      setIsLoadingTimeSeries(false);
    };

    fetchInitialData();
    return () => controller.abort();
  }, []); // Only run once on mount

  useEffect(() => {
    if (timeSeriesView !== 'monthly') {
      return;
    }

    const controller = new AbortController();
    const fetchMonthlyTimeSeries = async () => {
      setIsLoadingMonthly(true);
      try {
        const response = await fetch(
          `${API_BASE_URL}/analytics/time-series/monthly?year=${selectedYear}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        setMonthlyTimeSeries(payload.items ?? []);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch monthly time series data', error);
        setMonthlyTimeSeries([]);
      } finally {
        setIsLoadingMonthly(false);
      }
    };

    fetchMonthlyTimeSeries();
    return () => controller.abort();
  }, [timeSeriesView, selectedYear]);

  useEffect(() => {
    setHoveredPoint(null);
  }, [timeSeriesView, selectedYear]);

  // Fetch map points with filters (for map view only)
  useEffect(() => {
    const controller = new AbortController();
    const fetchMapPoints = async () => {
      setIsLoadingMap(true);
      try {
        const params = new URLSearchParams({
          limit: '400',
          severity_min: String(mapSeverityMin),
          severity_max: String(mapSeverityMax),
        });
        if (mapSunFilter !== 'ALL') {
          params.append('sun_filter', mapSunFilter);
        }
        const response = await fetch(
          `${API_BASE_URL}/analytics/map/cities?${params.toString()}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        setMapPoints(payload.items ?? []);
        setMapError(null);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch map data', error);
        setMapPoints([]);
        setMapError('Unable to load map data right now.');
      } finally {
        setIsLoadingMap(false);
      }
    };

    fetchMapPoints();

    return () => controller.abort();
  }, [mapSunFilter, mapSeverityMin, mapSeverityMax]);

  // Fetch all map points without filters (for severity distribution)
  useEffect(() => {
    const controller = new AbortController();
    const fetchAllMapPoints = async () => {
      setIsLoadingAllMapPoints(true);
      try {
        const params = new URLSearchParams({
          limit: '2000', // Get more points for accurate distribution
        });
        const response = await fetch(
          `${API_BASE_URL}/analytics/map/cities?${params.toString()}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        setAllMapPoints(payload.items ?? []);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch all map data for severity distribution', error);
        setAllMapPoints([]);
      } finally {
        setIsLoadingAllMapPoints(false);
      }
    };

    fetchAllMapPoints();

    return () => controller.abort();
  }, []);

  // Fetch map points for weather pie chart (only sun filter, no severity filter)
  useEffect(() => {
    const controller = new AbortController();
    const fetchWeatherPiePoints = async () => {
      setIsLoadingWeatherPie(true);
      try {
        const params = new URLSearchParams({
          limit: '2000', // Get more points for accurate distribution
          severity_min: '1',
          severity_max: '4', // Include all severities
        });
        if (weatherPieSunFilter !== 'ALL') {
          params.append('sun_filter', weatherPieSunFilter);
        }
        const response = await fetch(
          `${API_BASE_URL}/analytics/map/cities?${params.toString()}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        setWeatherPiePoints(payload.items ?? []);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch weather pie data', error);
        setWeatherPiePoints([]);
      } finally {
        setIsLoadingWeatherPie(false);
      }
    };

    fetchWeatherPiePoints();

    return () => controller.abort();
  }, [weatherPieSunFilter]);

  // Fetch weather distribution when metric changes
  useEffect(() => {
    const controller = new AbortController();
    const fetchWeatherDistribution = async () => {
      setIsLoadingWeatherDist(true);
      try {
        const response = await fetch(
          `${API_BASE_URL}/analytics/weather-distribution?metric=${selectedWeatherMetric}&bins=10`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = await response.json();
        setWeatherDistribution(payload.items ?? []);
        setWeatherDistError(null);
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch weather distribution', error);
        setWeatherDistribution([]);
        setWeatherDistError('Unable to load weather distribution right now.');
      } finally {
        setIsLoadingWeatherDist(false);
      }
    };

    fetchWeatherDistribution();
    return () => controller.abort();
  }, [selectedWeatherMetric]);

  // Show loading screen if data is not ready
  if (!isDataReady) {
    return (
      <div className="app">
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: '#1a1a1a',
          color: '#ffffff',
          padding: '2rem'
        }}>
          <div style={{
            textAlign: 'center',
            maxWidth: '600px'
          }}>
            <h1 style={{
              fontSize: '2.5rem',
              marginBottom: '1rem',
              fontWeight: 'bold'
            }}>US ACCIDENT ANALYTICS</h1>
            
            <div style={{
              marginTop: '3rem',
              marginBottom: '2rem'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                border: '4px solid #333',
                borderTop: '4px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 2rem'
              }}></div>
              
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
              
              <h2 style={{
                fontSize: '1.5rem',
                marginBottom: '1rem',
                color: '#e5e7eb'
              }}>Loading Datasets</h2>
              
              <p style={{
                fontSize: '1rem',
                color: '#9ca3af',
                marginBottom: '0.5rem'
              }}>{loadingProgress}</p>
              
              {loadingError && (
                <p style={{
                  fontSize: '0.9rem',
                  color: '#ef4444',
                  marginTop: '1rem'
                }}>{loadingError}</p>
              )}
              
              <p style={{
                fontSize: '0.875rem',
                color: '#6b7280',
                marginTop: '2rem'
              }}>
                This may take 1-2 minutes on first startup...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>US ACCIDENT ANALYTICS</h1>
        </div>
      </header>

      <main className="dashboard">
        <section className="left-panel">
          <div className="card">
            <div className="panel-header">
              <h2>Map View</h2>
              <span className="panel-subtitle">Heatmap of accidents</span>
            </div>
            <div className="card-controls">
              <div className="filter-group">
                <label htmlFor="map-sun-filter">Sun Position</label>
                <select
                  id="map-sun-filter"
                  value={mapSunFilter}
                  onChange={(event) => setMapSunFilter(event.target.value)}
                >
                  <option value="ALL">All times</option>
                  <option value="Day">Day</option>
                  <option value="Night">Night</option>
                </select>
              </div>
              <div className="filter-group">
                <label htmlFor="map-severity-min">Severity Min</label>
                <select
                  id="map-severity-min"
                  value={mapSeverityMin}
                  onChange={(event) => {
                    const next = Number(event.target.value);
                    setMapSeverityMin(next);
                    if (next > mapSeverityMax) {
                      setMapSeverityMax(next);
                    }
                  }}
                >
                  {[1, 2, 3, 4].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
              <div className="filter-group">
                <label htmlFor="map-severity-max">Severity Max</label>
                <select
                  id="map-severity-max"
                  value={mapSeverityMax}
                  onChange={(event) => {
                    const next = Number(event.target.value);
                    setMapSeverityMax(next);
                    if (next < mapSeverityMin) {
                      setMapSeverityMin(next);
                    }
                  }}
                >
                  {[1, 2, 3, 4].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {isLoadingMap ? (
              <div className="map-placeholder">
                <div className="map-placeholder__overlay">
                  <p>Loading map data…</p>
                </div>
              </div>
            ) : mapError ? (
              <div className="map-placeholder">
                <div className="map-placeholder__overlay">
                  <p className="error">{mapError}</p>
                </div>
              </div>
            ) : mapPoints.length === 0 ? (
              <div className="map-placeholder">
                <div className="map-placeholder__overlay">
                  <p className="placeholder">No map data available.</p>
                </div>
              </div>
            ) : (
              <div className="map-container">
                <AccidentHeatmap points={mapPoints} />
                <div className="map-legend">
                  <div className="map-legend__item">
                    <span className="map-legend__swatch map-legend__swatch--high" />
                    <span>Higher accident concentration</span>
                  </div>
                  <div className="map-legend__item">
                    <span className="map-legend__swatch map-legend__swatch--low" />
                    <span>Lower accident concentration</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <div className="chart-card__header">
              <h4>Severity Distribution</h4>
              <select
                className="chart-card__filter"
                value={severityGraphFilter}
                onChange={(e) => setSeverityGraphFilter(e.target.value)}
              >
                <option value="COUNT">By Count</option>
                <option value="PERCENT">By Percentage</option>
              </select>
            </div>
            <div className="chart-card__content">
              <div className="severity-chart-large">
                {severityDistribution.map((item) => {
                  const displayValue =
                    severityGraphFilter === 'PERCENT'
                      ? `${item.percentage.toFixed(1)}%`
                      : numberFormatter.format(item.count);
                  const maxValue = Math.max(
                    ...severityDistribution.map((d) =>
                      severityGraphFilter === 'PERCENT' ? d.percentage : d.count
                    )
                  );
                  const barWidth =
                    maxValue > 0
                      ? ((severityGraphFilter === 'PERCENT' ? item.percentage : item.count) /
                          maxValue) *
                        100
                      : 0;
                  const severityColors = {
                    1: '#22c55e',
                    2: '#eab308',
                    3: '#f97316',
                    4: '#dc2626',
                  };
                  return (
                    <div key={item.severity} className="severity-bar-large">
                      <div className="severity-bar-large__label-group">
                        <span className="severity-bar-large__label">Severity {item.severity}</span>
                        <span className="severity-bar-large__value">{displayValue}</span>
                      </div>
                      <div className="severity-bar-large__track">
                        <div
                          className="severity-bar-large__fill"
                          style={{
                            width: `${barWidth}%`,
                            backgroundColor: severityColors[item.severity],
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="chart-card__header">
              <h4>Annual Trend</h4>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <select
                  className="chart-card__filter"
                  value={timeSeriesView}
                  onChange={(e) => {
                    setTimeSeriesView(e.target.value);
                    setHoveredPoint(null);
                  }}
                >
                  <option value="annual">Annual View</option>
                  <option value="monthly">Monthly View</option>
                </select>
                {timeSeriesView === 'monthly' && (
                  <select
                    className="chart-card__filter"
                    value={selectedYear}
                    onChange={(e) => {
                      setSelectedYear(Number(e.target.value));
                      setHoveredPoint(null);
                    }}
                  >
                    {[2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023].map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
            <div className="chart-card__content">
              {timeSeriesView === 'annual' ? (
                isLoadingTimeSeries ? (
                  <div className="chart-loading">Loading trend data…</div>
                ) : timeSeriesError ? (
                  <div className="chart-error">{timeSeriesError}</div>
                ) : timeSeries.length === 0 ? (
                  <div className="chart-error">No trend data available</div>
                ) : (
                  <div className="line-chart">
                  <svg viewBox="0 0 400 300" className="line-chart__svg" preserveAspectRatio="xMidYMid meet">
                    <defs>
                      <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                        <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
                      </linearGradient>
                    </defs>
                    <g className="line-chart__grid">
                      {[0, 1, 2, 3, 4].map((i) => (
                        <line
                          key={i}
                          x1="10"
                          y1={40 + i * 55}
                          x2="390"
                          y2={40 + i * 55}
                          stroke="rgba(148, 163, 184, 0.1)"
                          strokeWidth="1"
                        />
                      ))}
                    </g>
                    <polygon
                      className="line-chart__area"
                      fill="url(#lineGradient)"
                      points={`10,260 ${timeSeries
                        .map((point, index) => {
                          const maxValue = Math.max(...timeSeries.map((p) => p.total_accidents));
                          const x = 10 + (index / (timeSeries.length - 1 || 1)) * 380;
                          const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                          return `${x},${y}`;
                        })
                        .join(' ')} 390,260`}
                    />
                    <polyline
                      className="line-chart__line"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={timeSeries
                        .map((point, index) => {
                          const maxValue = Math.max(...timeSeries.map((p) => p.total_accidents));
                          const x = 10 + (index / (timeSeries.length - 1 || 1)) * 380;
                          const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                          return `${x},${y}`;
                        })
                        .join(' ')}
                    />
                    {timeSeries.map((point, index) => {
                      const maxValue = Math.max(...timeSeries.map((p) => p.total_accidents));
                      const x = 10 + (index / (timeSeries.length - 1 || 1)) * 380;
                      const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                      return (
                        <g key={point.year}>
                          <circle
                            cx={x}
                            cy={y}
                            r={hoveredPoint === index ? "6" : "4"}
                            fill={hoveredPoint === index ? "#60a5fa" : "#3b82f6"}
                            stroke="#0f172a"
                            strokeWidth="2"
                            className="line-chart__point"
                            onMouseEnter={() => setHoveredPoint(index)}
                            onMouseLeave={() => setHoveredPoint(null)}
                            style={{ cursor: 'pointer', transition: 'r 0.2s ease, fill 0.2s ease' }}
                          />
                          <text
                            x={x}
                            y="290"
                            textAnchor="middle"
                            className="line-chart__label"
                          >
                            {point.year.toString().slice(-2)}
                          </text>
                        </g>
                      );
                    })}
                    {hoveredPoint !== null && (
                      <g className="line-chart__tooltip-group">
                        <rect
                          x={10 + (hoveredPoint / (timeSeries.length - 1 || 1)) * 380 - 50}
                          y={300 - 40 - ((timeSeries[hoveredPoint].total_accidents / (Math.max(...timeSeries.map((p) => p.total_accidents)) || 1)) * 220) - 35}
                          width="100"
                          height="30"
                          rx="4"
                          fill="rgba(15, 23, 42, 0.95)"
                          stroke="rgba(148, 163, 184, 0.3)"
                          strokeWidth="1"
                        />
                        <text
                          x={10 + (hoveredPoint / (timeSeries.length - 1 || 1)) * 380}
                          y={300 - 40 - ((timeSeries[hoveredPoint].total_accidents / (Math.max(...timeSeries.map((p) => p.total_accidents)) || 1)) * 220) - 15}
                          textAnchor="middle"
                          className="line-chart__tooltip-text"
                        >
                          {timeSeries[hoveredPoint].year}: {numberFormatter.format(timeSeries[hoveredPoint].total_accidents)}
                        </text>
                      </g>
                    )}
                    <g className="line-chart__y-axis">
                      {[0, 1, 2, 3, 4].map((i) => {
                        const maxValue = Math.max(...timeSeries.map((p) => p.total_accidents));
                        const value = maxValue - (i / 4) * maxValue;
                        return (
                          <text
                            key={i}
                            x="5"
                            y={45 + i * 55}
                            textAnchor="end"
                            className="line-chart__axis-label"
                          >
                            {numberFormatter.format(value)}
                          </text>
                        );
                      })}
                    </g>
                  </svg>
                  <div className="line-chart__summary">
                    <div className="line-chart__summary-item">
                      <span className="line-chart__summary-label">Peak Year</span>
                      <span className="line-chart__summary-value">
                        {timeSeries.reduce((max, p) => (p.total_accidents > max.total_accidents ? p : max), timeSeries[0])?.year || 'N/A'}
                      </span>
                    </div>
                    <div className="line-chart__summary-item">
                      <span className="line-chart__summary-label">Total</span>
                      <span className="line-chart__summary-value">
                        {numberFormatter.format(timeSeries.reduce((sum, p) => sum + p.total_accidents, 0))}
                      </span>
                    </div>
                  </div>
                </div>
                )
              ) : (
                isLoadingMonthly ? (
                  <div className="chart-loading">Loading monthly data…</div>
                ) : monthlyTimeSeries.length === 0 ? (
                  <div className="chart-error">No monthly data available</div>
                ) : (
                  <div className="line-chart">
                    <svg viewBox="0 0 400 300" className="line-chart__svg" preserveAspectRatio="xMidYMid meet">
                      <defs>
                        <linearGradient id="lineGradientMonthly" x1="0%" y1="0%" x2="0%" y2="100%">
                          <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                          <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
                        </linearGradient>
                      </defs>
                      <g className="line-chart__grid">
                        {[0, 1, 2, 3, 4].map((i) => (
                          <line
                            key={i}
                            x1="10"
                            y1={40 + i * 55}
                            x2="390"
                            y2={40 + i * 55}
                            stroke="rgba(148, 163, 184, 0.1)"
                            strokeWidth="1"
                          />
                        ))}
                      </g>
                      <polygon
                        className="line-chart__area"
                        fill="url(#lineGradientMonthly)"
                        points={`10,260 ${monthlyTimeSeries
                          .map((point, index) => {
                            const maxValue = Math.max(...monthlyTimeSeries.map((p) => p.total_accidents));
                            const x = 10 + (index / (monthlyTimeSeries.length - 1 || 1)) * 380;
                            const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                            return `${x},${y}`;
                          })
                          .join(' ')} 390,260`}
                      />
                      <polyline
                        className="line-chart__line"
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        points={monthlyTimeSeries
                          .map((point, index) => {
                            const maxValue = Math.max(...monthlyTimeSeries.map((p) => p.total_accidents));
                            const x = 10 + (index / (monthlyTimeSeries.length - 1 || 1)) * 380;
                            const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                            return `${x},${y}`;
                          })
                          .join(' ')}
                      />
                      {monthlyTimeSeries.map((point, index) => {
                        const maxValue = Math.max(...monthlyTimeSeries.map((p) => p.total_accidents));
                        const x = 10 + (index / (monthlyTimeSeries.length - 1 || 1)) * 380;
                        const y = 300 - 40 - ((point.total_accidents / (maxValue || 1)) * 220);
                        return (
                          <g key={point.month}>
                            <circle
                              cx={x}
                              cy={y}
                              r={hoveredPoint === index ? "6" : "4"}
                              fill={hoveredPoint === index ? "#60a5fa" : "#3b82f6"}
                              stroke="#0f172a"
                              strokeWidth="2"
                              className="line-chart__point"
                              onMouseEnter={() => setHoveredPoint(index)}
                              onMouseLeave={() => setHoveredPoint(null)}
                              style={{ cursor: 'pointer', transition: 'r 0.2s ease, fill 0.2s ease' }}
                            />
                            <text
                              x={x}
                              y="290"
                              textAnchor="middle"
                              className="line-chart__label"
                            >
                              {point.month_name}
                            </text>
                          </g>
                        );
                      })}
                      {hoveredPoint !== null && monthlyTimeSeries[hoveredPoint] && (
                        <g className="line-chart__tooltip-group">
                          <rect
                            x={10 + (hoveredPoint / (monthlyTimeSeries.length - 1 || 1)) * 380 - 60}
                            y={300 - 40 - ((monthlyTimeSeries[hoveredPoint].total_accidents / (Math.max(...monthlyTimeSeries.map((p) => p.total_accidents)) || 1)) * 220) - 35}
                            width="120"
                            height="30"
                            rx="4"
                            fill="rgba(15, 23, 42, 0.95)"
                            stroke="rgba(148, 163, 184, 0.3)"
                            strokeWidth="1"
                          />
                          <text
                            x={10 + (hoveredPoint / (monthlyTimeSeries.length - 1 || 1)) * 380}
                            y={300 - 40 - ((monthlyTimeSeries[hoveredPoint].total_accidents / (Math.max(...monthlyTimeSeries.map((p) => p.total_accidents)) || 1)) * 220) - 15}
                            textAnchor="middle"
                            className="line-chart__tooltip-text"
                          >
                            {monthlyTimeSeries[hoveredPoint].month_name} {selectedYear}: {numberFormatter.format(monthlyTimeSeries[hoveredPoint].total_accidents)}
                          </text>
                        </g>
                      )}
                      <g className="line-chart__y-axis">
                        {[0, 1, 2, 3, 4].map((i) => {
                          const maxValue = Math.max(...monthlyTimeSeries.map((p) => p.total_accidents));
                          const value = maxValue - (i / 4) * maxValue;
                          return (
                            <text
                              key={i}
                              x="5"
                              y={45 + i * 55}
                              textAnchor="end"
                              className="line-chart__axis-label"
                            >
                              {numberFormatter.format(value)}
                            </text>
                          );
                        })}
                      </g>
                    </svg>
                    <div className="line-chart__summary">
                      <div className="line-chart__summary-item">
                        <span className="line-chart__summary-label">Peak Month</span>
                        <span className="line-chart__summary-value">
                          {monthlyTimeSeries.reduce((max, p) => (p.total_accidents > max.total_accidents ? p : max), monthlyTimeSeries[0])?.month_name || 'N/A'}
                        </span>
                      </div>
                      <div className="line-chart__summary-item">
                        <span className="line-chart__summary-label">Total</span>
                        <span className="line-chart__summary-value">
                          {numberFormatter.format(monthlyTimeSeries.reduce((sum, p) => sum + p.total_accidents, 0))}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="card">
            <div className="chart-card__header">
              <h4>Weather Distribution</h4>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <select
                  className="chart-card__filter"
                  value={selectedWeatherMetric}
                  onChange={(e) => {
                    setSelectedWeatherMetric(e.target.value);
                    setHoveredDistBar(null);
                  }}
                >
                  <option value="temperature">Temperature</option>
                  <option value="wind_speed">Wind Speed</option>
                  <option value="precipitation">Precipitation</option>
                  <option value="visibility">Visibility</option>
                </select>
              </div>
            </div>
            {isLoadingWeatherDist ? (
              <p className="placeholder">Loading distribution…</p>
            ) : weatherDistError ? (
              <p className="error">{weatherDistError}</p>
            ) : weatherDistribution.length === 0 ? (
              <p className="placeholder">No distribution data available.</p>
            ) : (
              <div className="chart-card__content">
                <div className="temperature-dist-chart">
                  <svg viewBox="0 0 500 350" className="temperature-dist-chart__svg" preserveAspectRatio="xMidYMid meet">
                    <defs>
                      <linearGradient id="tempDistGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(239, 68, 68, 0.6)" />
                        <stop offset="100%" stopColor="rgba(239, 68, 68, 0.2)" />
                      </linearGradient>
                      <linearGradient id="windDistGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(34, 197, 94, 0.6)" />
                        <stop offset="100%" stopColor="rgba(34, 197, 94, 0.2)" />
                      </linearGradient>
                      <linearGradient id="precipDistGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(168, 85, 247, 0.6)" />
                        <stop offset="100%" stopColor="rgba(168, 85, 247, 0.2)" />
                      </linearGradient>
                      <linearGradient id="visDistGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="rgba(59, 130, 246, 0.6)" />
                        <stop offset="100%" stopColor="rgba(59, 130, 246, 0.2)" />
                      </linearGradient>
                    </defs>
                    <g className="temperature-dist-chart__grid">
                      {[0, 1, 2, 3, 4].map((i) => (
                        <line
                          key={i}
                          x1="20"
                          y1={35 + i * 65}
                          x2="495"
                          y2={35 + i * 65}
                          stroke="rgba(148, 163, 184, 0.1)"
                          strokeWidth="1"
                        />
                      ))}
                    </g>
                    {(() => {
                      const maxCount = Math.max(...weatherDistribution.map((d) => d.count));
                      const barWidth = 475 / weatherDistribution.length;
                      
                      // Color scheme based on selected metric
                      const colorScheme = {
                        temperature: { fill: "rgba(239, 68, 68, 0.5)", stroke: "#ef4444", gradient: "tempDistGradient" },
                        wind_speed: { fill: "rgba(34, 197, 94, 0.5)", stroke: "#22c55e", gradient: "windDistGradient" },
                        precipitation: { fill: "rgba(168, 85, 247, 0.5)", stroke: "#a855f7", gradient: "precipDistGradient" },
                        visibility: { fill: "rgba(59, 130, 246, 0.5)", stroke: "#3b82f6", gradient: "visDistGradient" },
                      };
                      const colors = colorScheme[selectedWeatherMetric] || colorScheme.temperature;
                      
                      return weatherDistribution.map((item, idx) => {
                        const x = 20 + idx * barWidth;
                        const barHeight = (item.count / maxCount) * 260;
                        const y = 295 - barHeight;
                        const isHovered = hoveredDistBar === idx;
                        
                        // Extract label for display (remove units for compact display)
                        let labelText = item.temperature_range;
                        if (selectedWeatherMetric === 'temperature') {
                          labelText = item.temperature_range.split('°')[0] + '°';
                        } else if (selectedWeatherMetric === 'wind_speed') {
                          labelText = item.temperature_range.split(' ')[0];
                        } else if (selectedWeatherMetric === 'precipitation') {
                          labelText = item.temperature_range.split(' ')[0];
                        } else if (selectedWeatherMetric === 'visibility') {
                          labelText = item.temperature_range.split(' ')[0];
                        }
                        
                        return (
                          <g key={item.temperature_range}>
                            <rect
                              x={x + 2}
                              y={y}
                              width={barWidth - 4}
                              height={barHeight}
                              fill={isHovered ? `url(#${colors.gradient})` : colors.fill}
                              stroke={colors.stroke}
                              strokeWidth={isHovered ? "2" : "1"}
                              rx="3"
                              className="temperature-dist-chart__bar"
                              onMouseEnter={() => setHoveredDistBar(idx)}
                              onMouseLeave={() => setHoveredDistBar(null)}
                              style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                            />
                            <text
                              x={x + barWidth / 2}
                              y="335"
                              textAnchor="middle"
                              className="temperature-dist-chart__label"
                              transform={`rotate(-45 ${x + barWidth / 2} 335)`}
                            >
                              {labelText}
                            </text>
                            {isHovered && (
                              <g className="temperature-dist-chart__tooltip">
                                <rect
                                  x={x + barWidth / 2 - 60}
                                  y={y - 50}
                                  width="120"
                                  height="40"
                                  rx="4"
                                  fill="rgba(15, 23, 42, 0.95)"
                                  stroke="rgba(148, 163, 184, 0.3)"
                                  strokeWidth="1"
                                />
                                <text
                                  x={x + barWidth / 2}
                                  y={y - 30}
                                  textAnchor="middle"
                                  className="temperature-dist-chart__tooltip-text"
                                >
                                  {item.temperature_range}
                                </text>
                                <text
                                  x={x + barWidth / 2}
                                  y={y - 15}
                                  textAnchor="middle"
                                  className="temperature-dist-chart__tooltip-value"
                                >
                                  {numberFormatter.format(item.count)} ({item.percentage}%)
                                </text>
                              </g>
                            )}
                          </g>
                        );
                      });
                    })()}
                    <g className="temperature-dist-chart__y-axis">
                      {[0, 1, 2, 3, 4].map((i) => {
                        const maxCount = Math.max(...weatherDistribution.map((d) => d.count));
                        const value = maxCount - (i / 4) * maxCount;
                        return (
                          <text
                            key={i}
                            x="15"
                            y={40 + i * 65}
                            textAnchor="end"
                            className="temperature-dist-chart__axis-label"
                          >
                            {numberFormatter.format(value)}
                          </text>
                        );
                      })}
                    </g>
                  </svg>
                </div>
              </div>
            )}
          </div>
        </section>

        <aside className="analytics-panel">
          <div className="card">
            <div className="card-header">
              <h3>
                {selectedState === STATE_ALL
                  ? `Top ${topLimit} States`
                  : `Top ${topLimit} Cities in ${selectedState}`}
              </h3>
              <span className="chip chip--primary">Total accidents</span>
            </div>
            <div className="card-controls">
              <div className="card-control">
                <label htmlFor="leaderboard-state">View</label>
                <select
                  id="leaderboard-state"
                  value={selectedState}
                  onChange={(event) => setSelectedState(event.target.value)}
                >
                  <option value={STATE_ALL}>Top states (nationwide)</option>
                  {availableStates.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </div>
              <div className="card-control">
                <label htmlFor="leaderboard-limit">Top N: {topLimit}</label>
                <input
                  id="leaderboard-limit"
                  type="range"
                  min="5"
                  max="20"
                  value={topLimit}
                  onChange={(event) => setTopLimit(Number(event.target.value))}
                />
              </div>
            </div>
            {isLoadingLeaderboard ? (
              <p className="placeholder">Loading leaderboard…</p>
            ) : leaderboardError ? (
              <p className="error">{leaderboardError}</p>
            ) : leaderboardItems.length === 0 ? (
              <p className="placeholder">No data for the selected view.</p>
            ) : (
              <ol className="list list--ordered">
                {leaderboardItems.map((item) => (
                  <li key={item.id}>
                    <span>
                      {item.label}
                      {item.description ? (
                        <span className="list__description"> · {item.description}</span>
                      ) : null}
                    </span>
                    <span className="metric">{numberFormatter.format(item.metric)}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>

          <div className="card">
            <div className="chart-card__header">
              <h3>Weather Conditions</h3>
              <select
                className="chart-card__filter"
                value={weatherPieSunFilter}
                onChange={(e) => setWeatherPieSunFilter(e.target.value)}
              >
                <option value="ALL">All times</option>
                <option value="Day">Day</option>
                <option value="Night">Night</option>
              </select>
            </div>
            <div className="chart-card__content">
              <div className="donut-chart">
                <svg viewBox="0 0 200 200" className="donut-chart__svg">
                  <circle
                    cx="100"
                    cy="100"
                    r="80"
                    fill="none"
                    stroke="rgba(30, 41, 59, 0.5)"
                    strokeWidth="30"
                  />
                  {(() => {
                    const circumference = 2 * Math.PI * 80;
                    return weatherConditionsComparison.map((item, index) => {
                      const offset = weatherConditionsComparison
                        .slice(0, index)
                        .reduce((sum, d) => sum + (d.percentage / 100) * circumference, 0);
                      const length = (item.percentage / 100) * circumference;
                      const isHovered = hoveredWeather === item.label;
                      return (
                        <circle
                          key={item.label}
                          cx="100"
                          cy="100"
                          r={isHovered ? "85" : "80"}
                          fill="none"
                          stroke={item.color}
                          strokeWidth={isHovered ? "35" : "30"}
                          strokeDasharray={`${length} ${circumference}`}
                          strokeDashoffset={-offset}
                          transform="rotate(-90 100 100)"
                          className="donut-chart__segment"
                          style={{
                            cursor: 'pointer',
                            transition: 'r 0.2s ease, stroke-width 0.2s ease, opacity 0.2s ease',
                            opacity: hoveredWeather === null || isHovered ? 1 : 0.4,
                            filter: isHovered ? 'drop-shadow(0 0 8px rgba(255,255,255,0.3))' : 'none',
                          }}
                          onMouseEnter={() => setHoveredWeather(item.label)}
                          onMouseLeave={() => setHoveredWeather(null)}
                        />
                      );
                    });
                  })()}
                  <text x="100" y="100" textAnchor="middle" className="donut-chart__center-text">
                    {hoveredWeather
                      ? `${weatherConditionsComparison.find((w) => w.label === hoveredWeather)?.percentage.toFixed(1) || '0'}%`
                      : weatherConditionsComparison.length > 0
                      ? `${weatherConditionsComparison[0].percentage.toFixed(1)}%`
                      : '0%'}
                  </text>
                  <text x="100" y="115" textAnchor="middle" className="donut-chart__center-label">
                    {hoveredWeather || weatherConditionsComparison[0]?.label || 'N/A'}
                  </text>
                </svg>
                <div className="donut-chart__legend">
                  {weatherConditionsComparison.map((item) => {
                    const isHovered = hoveredWeather === item.label;
                    return (
                      <div
                        key={item.label}
                        className="donut-chart__legend-item"
                        style={{
                          opacity: hoveredWeather === null || isHovered ? 1 : 0.5,
                          transform: isHovered ? 'translateX(4px)' : 'translateX(0)',
                          transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={() => setHoveredWeather(item.label)}
                        onMouseLeave={() => setHoveredWeather(null)}
                      >
                        <span
                          className="donut-chart__legend-dot"
                          style={{
                            backgroundColor: item.color,
                            transform: isHovered ? 'scale(1.2)' : 'scale(1)',
                            transition: 'transform 0.2s ease',
                          }}
                        />
                        <span className="donut-chart__legend-label">{item.label}</span>
                        <span className="donut-chart__legend-value">
                          {numberFormatter.format(item.count)} ({item.percentage.toFixed(1)}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </aside>
      </main>

      <footer className="app__footer">
        <span>Dataset © Kaggle</span>
        <span>Built with React + Leaflet (prototype)</span>
      </footer>
    </div>
  );
}

export default App;
