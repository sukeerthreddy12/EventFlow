import { Link } from "react-router-dom";
import type { PublicEvent } from "../../api/events";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function priceLabel(price: string) {
  return Number(price) === 0 ? "Free" : `$${price}`;
}

type Props = {
  events: PublicEvent[];
  linkPrefix?: string;
  emptyMessage?: string;
};

export default function EventShowcase({
  events,
  linkPrefix = "/app/events",
  emptyMessage = "No published events yet.",
}: Props) {
  if (events.length === 0) {
    return <p className="state-msg">{emptyMessage}</p>;
  }

  return (
    <ul className="event-showcase">
      {events.map((event, index) => (
        <li
          key={event.id}
          className={
            event.is_featured
              ? "event-showcase__item event-showcase__item--featured"
              : "event-showcase__item"
          }
          style={{ animationDelay: `${0.06 * index}s` }}
        >
          <Link to={`${linkPrefix}/${event.id}`} className="event-showcase__link">
            <div className="event-showcase__index">
              {String(index + 1).padStart(2, "0")}
            </div>
            <div className="event-showcase__body">
              <div className="event-showcase__top">
                <h3 className="event-showcase__title">{event.title}</h3>
                <span className="event-showcase__price">
                  {priceLabel(event.price)}
                </span>
              </div>
              {event.description ? (
                <p className="event-showcase__desc">
                  {event.description.length > 110
                    ? `${event.description.slice(0, 109)}…`
                    : event.description}
                </p>
              ) : null}
              <div className="event-showcase__meta">
                <span>{formatWhen(event.starts_at)}</span>
                <span>{event.venue}</span>
                <span>{event.max_capacity} capacity</span>
                {event.is_featured ? (
                  <span className="event-showcase__featured-tag">Featured</span>
                ) : null}
              </div>
            </div>
            <span className="event-showcase__arrow" aria-hidden="true">
              →
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
