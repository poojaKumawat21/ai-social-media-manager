import React, { useEffect, useMemo, useState } from "react";
import api from "../services/api";
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

function ContentCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date());

  const [selectedDate, setSelectedDate] = useState(null);

  const [posts, setPosts] = useState([]);

  useEffect(() => {
    const fetchScheduledPosts = async () => {
      try {
        const scheduledResult = await api.get("/scheduled-posts");
        const postsResult = await api.get("/posts");

        const allPosts = postsResult.posts || [];

        const postMap = new Map(
          allPosts.map((post) => [post.id, post])
        );

        const formattedPosts = (
          scheduledResult.scheduled_posts || []
        ).map((scheduledPost) => {
          const post =
            postMap.get(scheduledPost.post_id) || {};

          const scheduledDate = new Date(
            scheduledPost.scheduled_at
          );

          const date = `${scheduledDate.getFullYear()}-${String(
            scheduledDate.getMonth() + 1
          ).padStart(2, "0")}-${String(
            scheduledDate.getDate()
          ).padStart(2, "0")}`;

          return {
            id: scheduledPost.id,

            title:
              post.post_idea ||
              post.topic ||
              "Scheduled Post",

            platform:
              scheduledPost.platform === "linkedin"
                ? PLATFORM.LINKEDIN
                : scheduledPost.platform,

            status: STATUS.SCHEDULED,

            date,

            time: scheduledDate.toLocaleTimeString(
              "en-US",
              {
                hour: "numeric",
                minute: "2-digit",
              }
            ),
          };
        });

        setPosts(formattedPosts);
      } catch (error) {
        console.error(
          "Failed to fetch calendar posts:",
          error
        );
      }
    };

    fetchScheduledPosts();
  }, []);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const monthName = currentDate.toLocaleString("en-US", {
    month: "long",
  });

  const calendarDays = useMemo(() => {
    const firstDay = new Date(
      year,
      month,
      1
    ).getDay();

    const daysInMonth = new Date(
      year,
      month + 1,
      0
    ).getDate();

    const previousMonthDays = new Date(
      year,
      month,
      0
    ).getDate();

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
    for (
      let day = 1;
      day <= daysInMonth;
      day++
    ) {
      const date = `${year}-${String(
        month + 1
      ).padStart(2, "0")}-${String(day).padStart(
        2,
        "0"
      )}`;

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

    return posts.filter(
      (post) => post.date === date
    );
  };

  const goToPreviousMonth = () => {
    setCurrentDate(
      new Date(year, month - 1, 1)
    );
  };

  const goToNextMonth = () => {
    setCurrentDate(
      new Date(year, month + 1, 1)
    );
  };

  const goToToday = () => {
    const today = new Date();

    setCurrentDate(
      new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      )
    );

    setSelectedDate(
      `${today.getFullYear()}-${String(
        today.getMonth() + 1
      ).padStart(2, "0")}-${String(
        today.getDate()
      ).padStart(2, "0")}`
    );
  };

  const isToday = (date) => {
    if (!date) return false;

    const today = new Date();

    const todayString = `${today.getFullYear()}-${String(
      today.getMonth() + 1
    ).padStart(2, "0")}-${String(
      today.getDate()
    ).padStart(2, "0")}`;

    return date === todayString;
  };

  return (
    <div className="content-calendar-page">

      {/* PAGE HEADER */}
      <div className="page-header">
        <div>
          <span className="calendar-label">
            CONTENT MANAGEMENT
          </span>

          <h1>Content Calendar</h1>

          <p>
            Plan, organize and schedule your social media content.
          </p>
        </div>

        <button
          className="primary-btn"
          onClick={() =>
            alert(
              "Schedule Post form will be connected later."
            )
          }
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

            <button
              onClick={goToPreviousMonth}
            >
              ←
            </button>

            <button
              onClick={goToToday}
            >
              Today
            </button>

            <button
              onClick={goToNextMonth}
            >
              →
            </button>

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

          {calendarDays.map(
            (calendarDay, index) => {
              const dayPosts =
                getPostsForDate(
                  calendarDay.date
                );

              const selected =
                selectedDate ===
                calendarDay.date;

              return (
                <div
                  key={`${
                    calendarDay.date ||
                    "outside"
                  }-${index}`}
                  className={`calendar-day
                    ${
                      calendarDay.outside
                        ? "outside-month"
                        : ""
                    }
                    ${
                      selected
                        ? "selected-day"
                        : ""
                    }
                    ${
                      isToday(
                        calendarDay.date
                      )
                        ? "today"
                        : ""
                    }
                  `}
                  onClick={() => {
                    if (
                      !calendarDay.outside
                    ) {
                      setSelectedDate(
                        calendarDay.date
                      );
                    }
                  }}
                >

                  <div className="calendar-day-number">
                    {calendarDay.day}
                  </div>

                  <div className="calendar-posts">

                    {dayPosts.map(
                      (post) => (
                        <div
                          key={post.id}
                          className={`calendar-post status-${post.status.toLowerCase()}`}
                        >

                          <div className="calendar-post-title">
                            {post.title}
                          </div>

                          <div className="calendar-post-meta">
                            <span>
                              {post.platform}
                            </span>

                            <span>
                              {post.time}
                            </span>
                          </div>

                        </div>
                      )
                    )}

                  </div>

                </div>
              );
            }
          )}

        </div>

        {/* SELECTED DATE */}
        {selectedDate && (
          <div className="selected-date-panel">

            <div>
              <span>
                SELECTED DATE
              </span>

              <strong>
                {new Date(
                  `${selectedDate}T00:00:00`
                ).toLocaleDateString(
                  "en-US",
                  {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  }
                )}
              </strong>
            </div>

            <button
              onClick={() =>
                alert(
                  "Create Post flow will be connected later."
                )
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