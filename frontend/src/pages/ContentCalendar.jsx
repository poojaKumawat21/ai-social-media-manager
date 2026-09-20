import React, { useMemo, useState } from "react";
import "./ContentCalendar.css";

const STATUS = {
  SCHEDULED: "SCHEDULED",
  DRAFT: "DRAFT",
  PUBLISHED: "PUBLISHED",
};

const PLATFORM = {
  INSTAGRAM: "Instagram",
  LINKEDIN: "LinkedIn",
  FACEBOOK: "Facebook",
  X: "X",
};

// Temporary UI data only.
// Later this will come from the backend API.
const INITIAL_POSTS = [
  {
    id: "post-001",
    title: "The Future of AI",
    platform: PLATFORM.INSTAGRAM,
    status: STATUS.SCHEDULED,
    date: "2026-09-16",
    time: "10:30 AM",
  },
  {
    id: "post-002",
    title: "5 AI Trends to Watch",
    platform: PLATFORM.LINKEDIN,
    status: STATUS.SCHEDULED,
    date: "2026-09-18",
    time: "06:00 PM",
  },
  {
    id: "post-003",
    title: "AI Productivity Tips",
    platform: PLATFORM.FACEBOOK,
    status: STATUS.DRAFT,
    date: "2026-09-21",
    time: "12:00 PM",
  },
  {
    id: "post-004",
    title: "Building with Generative AI",
    platform: PLATFORM.X,
    status: STATUS.SCHEDULED,
    date: "2026-09-24",
    time: "08:00 PM",
  },
];

function ContentCalendar() {
  const [currentDate, setCurrentDate] = useState(
    new Date(2026, 8, 1)
  );

  const [selectedDate, setSelectedDate] = useState(null);

  const [posts] = useState(INITIAL_POSTS);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const monthName = currentDate.toLocaleString("en-US", {
    month: "long",
  });

  const calendarDays = useMemo(() => {
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const previousMonthDays = new Date(year, month, 0).getDate();

    const days = [];

    // Previous month
    for (let i = firstDay - 1; i >= 0; i--) {
      days.push({
        day: previousMonthDays - i,
        date: null,
        outside: true,
      });
    }

    // Current month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = `${year}-${String(month + 1).padStart(2, "0")}-${String(
        day
      ).padStart(2, "0")}`;

      days.push({
        day,
        date,
        outside: false,
      });
    }

    // Next month
    let nextDay = 1;

    while (days.length < 42) {
      days.push({
        day: nextDay,
        date: null,
        outside: true,
      });

      nextDay++;
    }

    return days;
  }, [year, month]);

  const getPostsForDate = (date) => {
    if (!date) return [];

    return posts.filter((post) => post.date === date);
  };

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const goToToday = () => {
    const today = new Date();

    setCurrentDate(
      new Date(today.getFullYear(), today.getMonth(), 1)
    );

    setSelectedDate(
      `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(
        2,
        "0"
      )}-${String(today.getDate()).padStart(2, "0")}`
    );
  };

  const isToday = (date) => {
    if (!date) return false;

    const today = new Date();

    const todayString = `${today.getFullYear()}-${String(
      today.getMonth() + 1
    ).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

    return date === todayString;
  };

  return (
    <div className="content-calendar-page">

      {/* PAGE HEADER */}
      <div className="page-header">
        <div>
          <span className="calendar-label">CONTENT MANAGEMENT</span>

          <h1>Content Calendar</h1>

          <p>
            Plan, organize and schedule your social media content.
          </p>
        </div>

        <button
          className="primary-btn"
          onClick={() => alert("Schedule Post form will be connected later.")}
        >
          + Schedule Post
        </button>
      </div>

      {/* CALENDAR CARD */}
      <div className="calendar-card">

        {/* TOP BAR */}
        <div className="calendar-top">

          <div>
            <h3>
              {monthName} {year}
            </h3>

            <p>
              Your scheduled and planned content
            </p>
          </div>

          <div className="calendar-controls">
            <button onClick={goToPreviousMonth}>←</button>

            <button onClick={goToToday}>Today</button>

            <button onClick={goToNextMonth}>→</button>
          </div>

        </div>

        {/* WEEK DAYS */}
        <div className="calendar-weekdays">
          {[
            "Sun",
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
          ].map((day) => (
            <div key={day}>{day}</div>
          ))}
        </div>

        {/* CALENDAR GRID */}
        <div className="calendar-grid">

          {calendarDays.map((calendarDay, index) => {
            const dayPosts = getPostsForDate(calendarDay.date);

            const selected =
              selectedDate === calendarDay.date;

            return (
              <div
                key={`${calendarDay.date || "outside"}-${index}`}
                className={`calendar-day
                  ${calendarDay.outside ? "outside-month" : ""}
                  ${selected ? "selected-day" : ""}
                  ${isToday(calendarDay.date) ? "today" : ""}
                `}
                onClick={() => {
                  if (!calendarDay.outside) {
                    setSelectedDate(calendarDay.date);
                  }
                }}
              >

                <div className="calendar-day-number">
                  {calendarDay.day}
                </div>

                <div className="calendar-posts">

                  {dayPosts.map((post) => (
                    <div
                      key={post.id}
                      className={`calendar-post status-${post.status.toLowerCase()}`}
                    >
                      <div className="calendar-post-title">
                        {post.title}
                      </div>

                      <div className="calendar-post-meta">
                        <span>{post.platform}</span>
                        <span>{post.time}</span>
                      </div>
                    </div>
                  ))}

                </div>

              </div>
            );
          })}

        </div>

        {/* SELECTED DATE */}
        {selectedDate && (
          <div className="selected-date-panel">

            <div>
              <span>SELECTED DATE</span>

              <strong>
                {new Date(
                  `${selectedDate}T00:00:00`
                ).toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
              </strong>
            </div>

            <button
              onClick={() =>
                alert("Create Post flow will be connected later.")
              }
            >
              + Add Post
            </button>

          </div>
        )}

      </div>

      {/* LEGEND */}
      <div className="calendar-legend">

        <div>
          <span className="legend-dot scheduled"></span>
          Scheduled
        </div>

        <div>
          <span className="legend-dot draft"></span>
          Draft
        </div>

        <div>
          <span className="legend-dot published"></span>
          Published
        </div>

      </div>

    </div>
  );
}

export default ContentCalendar;