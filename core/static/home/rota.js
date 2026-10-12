// Fair Rota Scheduler: keeps the setup and the visitor's actions, asks the server
// to replay them (the engine is deterministic), and renders the result.
// Names come from visitors, so everything is built with text nodes, never innerHTML.
(function () {
    var root = document.querySelector('[data-rota]');
    if (!root) return;

    var initial = JSON.parse(document.getElementById('rota-setup').textContent);
    var setup = JSON.parse(JSON.stringify(initial));
    var actions = [];
    var selected = null;
    var data = null;
    var MAX_DAYS = 60;
    var TYPE = { devotion: 'Devotion', music: 'Music', story: 'Real story' };
    var STATUS = { assigned: 'Assigned', approved: 'Approved', published: 'Published', missed: 'Missed', open: 'Open' };

    function $(sel) { return root.querySelector(sel); }
    function el(tag, attrs, children) {
        var node = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (k) {
            if (k === 'class') node.className = attrs[k];
            else if (k === 'text') node.textContent = attrs[k];
            else if (k.indexOf('on') === 0) node.addEventListener(k.slice(2), attrs[k]);
            else node.setAttribute(k, attrs[k]);
        });
        (children || []).forEach(function (c) { if (c) node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
        return node;
    }
    function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
    function toDate(iso) { var p = iso.split('-'); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
    function iso(d) { return d.toISOString().slice(0, 10); }
    function addDays(isoDay, n) { var d = toDate(isoDay); d.setUTCDate(d.getUTCDate() + n); return iso(d); }
    function nice(isoDay, opts) { return toDate(isoDay).toLocaleDateString('en-GB', Object.assign({ timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short' }, opts || {})); }
    function nameOf(id) {
        if (!id) return 'Reserve';
        var p = (data.people.concat(data.reviewers)).filter(function (x) { return x.id === id; })[0];
        return p ? p.name : id;
    }
    function csrf() { var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }
    function status(text) { $('[data-rota-status]').textContent = text || ''; }

    // ------------------------------------------------------------------ server
    function run() {
        status('Updating…');
        fetch(window.ROTA_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
            body: JSON.stringify(Object.assign({}, setup, { actions: actions })),
        }).then(function (r) {
            return r.json().then(function (body) { if (!r.ok) throw new Error(body.detail || 'Request failed'); return body; });
        }).then(function (body) {
            data = body; status(''); render();
        }).catch(function (err) { status(err.message); });
    }

    // ------------------------------------------------------------------ render
    function render() {
        $('[data-rota-today]').textContent = nice(data.today, { year: 'numeric' });
        $('[data-rota-reserve]').textContent = data.reserve;
        var advanced = actions.filter(function (a) { return a.type === 'advance'; }).length;
        $('[data-rota-advance]').disabled = advanced >= MAX_DAYS;
        renderCalendar(); renderDetail(); renderTeam(); renderLoad(); renderLog();
    }

    function renderCalendar() {
        var cal = $('[data-rota-cal]'); clear(cal);
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].forEach(function (d) { cal.appendChild(el('div', { class: 'rc-head', text: d })); });
        var start = toDate(data.today); var dow = (start.getUTCDay() + 6) % 7;
        var first = addDays(data.today, -dow);
        var last = addDays(data.today, 27);
        var byDay = {};
        data.slots.forEach(function (s) { (byDay[s.day] = byDay[s.day] || []).push(s); });
        for (var day = first; day <= last; day = addDays(day, 1)) {
            var past = day < data.today, isToday = day === data.today;
            var cell = el('div', { class: 'rc-day' + (past ? ' is-past' : '') + (isToday ? ' is-today' : ''), role: 'gridcell' },
                [el('span', { class: 'rc-date', text: toDate(day).getUTCDate() + (toDate(day).getUTCDate() === 1 || day === first ? ' ' + nice(day, { weekday: undefined, day: undefined, month: 'short' }) : '') })]);
            (byDay[day] || []).forEach(function (s) {
                var cls = 'rc-chip t-' + s.type + ' st-' + s.status + (s.source === 'reserve' ? ' is-reserve' : '') +
                    (s.will_miss ? ' is-miss' : '') + (selected === s.key ? ' is-selected' : '');
                var who = s.source === 'reserve' ? 'Reserve' : (s.status === 'missed' ? 'Missed' : nameOf(s.writer));
                cell.appendChild(el('button', {
                    type: 'button', class: cls, 'aria-pressed': selected === s.key ? 'true' : 'false',
                    'aria-label': TYPE[s.type] + ' on ' + nice(s.day) + ': ' + who + ', ' + (STATUS[s.status] || s.status),
                    onclick: function () { selected = s.key; renderCalendar(); renderDetail(); },
                }, [el('span', { class: 'rc-type', text: TYPE[s.type] }), el('span', { class: 'rc-who', text: who })]));
            });
            cal.appendChild(cell);
        }
    }

    function renderDetail() {
        var box = $('[data-rota-detail]'); clear(box);
        var s = data.slots.filter(function (x) { return x.key === selected; })[0];
        if (!s) { box.appendChild(el('p', { class: 'rota-hint', text: 'Select any slot in the calendar to see who got it, and why.' })); return; }
        box.appendChild(el('p', { class: 'eyebrow', text: TYPE[s.type] }));
        box.appendChild(el('h3', { class: 'rd-title', text: nice(s.day, { year: 'numeric' }) }));
        var facts = el('dl', { class: 'rd-facts' });
        [['Writer', s.source === 'reserve' ? 'Reserve piece' : (s.writer ? nameOf(s.writer) : 'Nobody')],
         ['Reviewer', nameOf(s.reviewer)], ['Status', (STATUS[s.status] || s.status) + (s.will_miss ? ' (writer will miss)' : '')],
         ['Draft due', nice(s.draft_due)], ['Review due', nice(s.review_due)]].forEach(function (f) {
            facts.appendChild(el('div', {}, [el('dt', { text: f[0] }), el('dd', { text: f[1] })]));
        });
        box.appendChild(facts);
        if (s.missed_by.length) box.appendChild(el('p', { class: 'rd-note', text: 'Missed by ' + s.missed_by.map(nameOf).join(', ') + '.' }));

        var ex = s.explanation;
        if (ex && ex.winner && s.source !== 'reserve') {
            box.appendChild(el('h4', { class: 'rd-why', text: 'Why ' + nameOf(ex.winner) + '?' }));
            var notes = [];
            if (ex.relaxed) notes.push('Nobody passed every rule, so the back-to-back rule was relaxed.');
            if (ex.tie_break) notes.push('Loads tied, so the person whose latest slot was earliest went first.');
            notes.forEach(function (n) { box.appendChild(el('p', { class: 'rd-note', text: n })); });
            var table = el('table', { class: 'rd-table' }, [el('thead', {}, [el('tr', {}, [
                el('th', { text: 'Writer' }), el('th', { text: 'A / K' }), el('th', { text: 'M' }), el('th', { text: 'L' })])])]);
            var tb = el('tbody');
            ex.candidates.forEach(function (c, i) {
                tb.appendChild(el('tr', { class: i === 0 ? 'is-winner' : '' }, [
                    el('td', { text: nameOf(c.id) + (i === 0 ? ' ✓' : '') }), el('td', { text: c.held + ' / ' + c.capacity }),
                    el('td', { text: String(c.missed) }), el('td', { text: c.load.toFixed(2) })]));
            });
            table.appendChild(tb); box.appendChild(table);
            if (ex.excluded.length) {
                var ul = el('ul', { class: 'rd-excluded' });
                ex.excluded.forEach(function (x) { ul.appendChild(el('li', {}, [el('strong', { text: nameOf(x.id) + ': ' }), x.reason])); });
                box.appendChild(el('p', { class: 'rd-sub', text: 'Ruled out first' })); box.appendChild(ul);
            }
            box.appendChild(el('p', { class: 'rd-small', text: 'Load counted when the slot was assigned. Lowest wins; ties go to whoever has waited longest.' }));
        } else if (s.source === 'reserve') {
            box.appendChild(el('p', { class: 'rd-note', text: 'Too close to publishing to reassign, so a ready-made reserve piece fills the day.' }));
        }
        if (s.status === 'assigned' && !s.will_miss && s.writer) {
            box.appendChild(el('button', { type: 'button', class: 'btn btn-solid rd-miss', onclick: function () {
                actions.push({ type: 'miss', slot: s.key }); run();
            } }, [nameOf(s.writer) + ' will miss this deadline']));
            box.appendChild(el('p', { class: 'rd-small', text: 'Then advance past ' + nice(s.draft_due) + ' to see what happens.' }));
        }
    }

    function renderTeam() {
        var box = $('[data-rota-team]'); clear(box);
        setup.writers.forEach(function (w, i) {
            var row = el('div', { class: 'rt-row' });
            row.appendChild(el('input', { class: 'rt-name', value: w.name, maxlength: '30', 'aria-label': 'Name', onchange: function (e) {
                w.name = e.target.value.trim() || w.name; restart(); } }));
            row.appendChild(el('label', { class: 'rt-cap' }, ['Capacity ', el('input', { type: 'number', min: '1', max: '28', value: w.capacity, onchange: function (e) {
                w.capacity = Math.max(1, Math.min(28, parseInt(e.target.value, 10) || 1)); restart(); } })]));
            var off = el('div', { class: 'rt-off' });
            w.unavailable.slice().sort().forEach(function (d) {
                off.appendChild(el('button', { type: 'button', class: 'rt-day', title: 'Remove', onclick: function () {
                    w.unavailable = w.unavailable.filter(function (x) { return x !== d; }); restart(); } }, [nice(d) + ' ×']));
            });
            off.appendChild(el('input', { type: 'date', class: 'rt-add-day', min: setup.start, max: addDays(setup.start, 27), 'aria-label': 'Add a day off for ' + w.name, onchange: function (e) {
                if (e.target.value && w.unavailable.indexOf(e.target.value) === -1 && w.unavailable.length < 28) { w.unavailable.push(e.target.value); restart(); } } }));
            row.appendChild(off);
            if (setup.writers.length > 1) row.appendChild(el('button', { type: 'button', class: 'rt-remove', 'aria-label': 'Remove ' + w.name, onclick: function () {
                setup.writers.splice(i, 1); restart(); } }, ['×']));
            box.appendChild(row);
        });
        $('[data-rota-add]').hidden = setup.writers.length >= 8;
        $('[data-rota-reviewers]').textContent = 'Reviewers: ' + setup.reviewers.map(function (r) { return r.name; }).join(' and ') + '.';
    }

    function renderLoad() {
        var box = $('[data-rota-load]'); clear(box);
        data.people.forEach(function (p) {
            var pct = Math.min(100, p.load / 1.5 * 100);
            box.appendChild(el('div', { class: 'rl-row' }, [
                el('span', { class: 'rl-name', text: p.name }),
                el('span', { class: 'rl-bar' }, [el('i', { style: 'width:' + pct + '%' })]),
                el('span', { class: 'rl-val', text: p.held + '/' + p.capacity + (p.missed ? ' · ' + p.missed + ' missed' : '') + ' · L ' + p.load.toFixed(2) })]));
        });
    }

    function renderLog() {
        var box = $('[data-rota-log]'); clear(box);
        data.log.slice(0, 12).forEach(function (e) {
            box.appendChild(el('li', { class: 'lk-' + e.kind }, [el('span', { class: 'rl-day', text: nice(e.day) }), e.text]));
        });
    }

    function restart() { actions = []; selected = null; run(); }

    $('[data-rota-advance]').addEventListener('click', function () { actions.push({ type: 'advance' }); run(); });
    $('[data-rota-reset]').addEventListener('click', function () { setup = JSON.parse(JSON.stringify(initial)); restart(); });
    $('[data-rota-add]').addEventListener('click', function () {
        var n = setup.writers.length + 1, id = 'writer-' + Date.now().toString(36).slice(-6);
        setup.writers.push({ id: id, name: 'Writer ' + n, capacity: 8, unavailable: [] }); restart();
    });

    run();
})();
