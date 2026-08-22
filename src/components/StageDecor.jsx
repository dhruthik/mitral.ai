// Pure decoration: the furniture and knick-knacks that make the stage read as a
// room people hang out in rather than a grid of boxes. Nothing here is wired to
// state, so it is safe to rearrange — but keep it aria-hidden and
// pointer-events:none so it never gets between a user and an avatar.

const Plant = () => <svg width="46" height="62" viewBox="0 0 23 31" shapeRendering="crispEdges">
  <path d="M11 16V9" stroke="#2f7d5c" strokeWidth="2" />
  <path d="M11 12 6 8v4l5 4zM11 11l5-5v5l-5 4z" fill="#3ba274" />
  <path d="M11 9 8 3l3-2 3 2z" fill="#4fc08d" />
  <path d="M5 17h13l-2 11H7z" fill="#c86b4a" />
  <path d="M4 15h15v3H4z" fill="#e08a63" />
</svg>;

const Frame = ({ hue }) => <svg width="42" height="34" viewBox="0 0 21 17" shapeRendering="crispEdges">
  <rect width="21" height="17" rx="1" fill="#6b5a3e" />
  <rect x="2" y="2" width="17" height="13" fill={hue} />
  <path d="M2 15l5-6 3 3 4-5 5 8z" fill="#ffffff35" />
  <circle cx="6" cy="6" r="2" fill="#ffe9a8" />
</svg>;

// The house cat. Asleep through every deliberation, as is correct.
const Cat = () => <svg width="42" height="26" viewBox="0 0 21 13" shapeRendering="crispEdges">
  <path d="M4 12c0-4 3-6 6-6s6 2 6 6z" fill="#efd0a0" />
  <path d="M5 7 4 3l3 2zM12 5l3-2-1 4z" fill="#efd0a0" />
  <path d="M16 12c3 0 4-2 4-4" stroke="#efd0a0" strokeWidth="2" fill="none" />
  <path d="M7 9h2M12 9h2" stroke="#8a6b45" strokeWidth="1" />
  <circle cx="6" cy="10" r="1" fill="#e59aa8" />
  <circle cx="14" cy="10" r="1" fill="#e59aa8" />
</svg>;

const Mug = () => <svg width="20" height="18" viewBox="0 0 10 9" shapeRendering="crispEdges">
  <path d="M1 2h6v6H1z" fill="#fff" />
  <path d="M1 2h6v2H1z" fill="#e8687f" />
  <path d="M7 3h2v3H7z" fill="none" stroke="#fff" strokeWidth="1" />
</svg>;

const SPARKS = [[8, 22], [23, 12], [46, 8], [68, 15], [88, 26], [93, 54], [5, 48]];

export default function StageDecor() {
  return <div className="stage-decor" aria-hidden="true">
    <div className="garland" />
    <div className="frames"><Frame hue="#3b6ea5" /><Frame hue="#7a5cb8" /><Frame hue="#2f7d5c" /></div>
    <div className="plant left"><Plant /></div>
    <div className="plant right"><Plant /></div>
    <div className="cat"><Cat /></div>
    <div className="mug"><Mug /></div>
    {SPARKS.map(([x, y], index) => <span
      key={index}
      className="twinkle"
      style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${index * .7}s` }}
    />)}
  </div>;
}
