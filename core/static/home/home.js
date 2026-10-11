// Home page interactions: mobile nav, ribbon pause, nav border, scroll reveal.
(function () {
    var nav = document.querySelector('.site-nav');
    var toggle = document.querySelector('.nav-toggle');
    var links = document.getElementById('nav-links');

    toggle.addEventListener('click', function () {
        var open = links.classList.toggle('open');
        toggle.setAttribute('aria-expanded', open);
    });
    links.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') {
            links.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
        }
    });

    window.addEventListener('scroll', function () {
        nav.classList.toggle('scrolled', window.scrollY > 8);
    }, { passive: true });

    // the role ribbon only exists on the home page
    var ribbon = document.querySelector('.ribbon');
    var pause = document.querySelector('.ribbon-pause');
    if (ribbon && pause) {
        pause.addEventListener('click', function () {
            var paused = ribbon.classList.toggle('paused');
            pause.setAttribute('aria-pressed', paused);
            pause.textContent = paused ? 'Play' : 'Pause';
        });
    }

    var items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) return;   // content simply stays visible

    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            // reveal on entering the viewport, or once it has been scrolled/jumped past
            if (entry.isIntersecting || entry.boundingClientRect.top < 0) {
                entry.target.classList.add('in');
                io.unobserve(entry.target);
            }
        });
    }, { rootMargin: '0px 0px -10% 0px' });
    items.forEach(function (el) { io.observe(el); });
    document.documentElement.classList.add('reveal-on');

    // a jump that skips straight over an element never fires the observer, so sweep on scroll
    var ticking = false;
    window.addEventListener('scroll', function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
            items.forEach(function (el) {
                if (!el.classList.contains('in') && el.getBoundingClientRect().top < window.innerHeight) {
                    el.classList.add('in');
                    io.unobserve(el);
                }
            });
            ticking = false;
        });
    }, { passive: true });
})();

// "Download PDF" buttons open the print dialog (Save as PDF)
document.querySelectorAll('[data-print]').forEach(function (btn) {
    btn.addEventListener('click', function () { window.print(); });
});

// copy-to-clipboard for the email address (for visitors without a mail app)
document.querySelectorAll('[data-copy]').forEach(function (btn) {
    var label = btn.querySelector('[data-copy-label]');
    var original = label ? label.textContent : '';
    btn.addEventListener('click', function () {
        var text = btn.getAttribute('data-copy');
        var done = function () {
            btn.classList.add('copied');
            if (label) label.textContent = 'Copied!';
            setTimeout(function () {
                btn.classList.remove('copied');
                if (label) label.textContent = original;
            }, 2000);
        };
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(done);
        } else {
            var t = document.createElement('textarea');
            t.value = text; t.style.position = 'fixed'; t.style.opacity = '0';
            document.body.appendChild(t); t.select();
            try { document.execCommand('copy'); done(); } catch (e) {}
            document.body.removeChild(t);
        }
    });
});

// Tiny projects hub: search + category + status filters (works for any number of cards)
(function () {
    var root = document.querySelector('[data-tp]');
    if (!root) return;
    var items = [].slice.call(root.querySelectorAll('[data-tp-item]'));
    var search = root.querySelector('[data-tp-search]');
    var count = root.querySelector('[data-tp-count]');
    var empty = root.querySelector('[data-tp-empty]');
    var state = { q: '', category: 'all', status: 'all' };

    function apply() {
        var shown = 0;
        items.forEach(function (el) {
            var ok = (state.category === 'all' || el.dataset.category === state.category) &&
                     (state.status === 'all' || el.dataset.status === state.status) &&
                     (!state.q || el.dataset.search.indexOf(state.q) !== -1);
            el.hidden = !ok;
            if (ok) shown++;
        });
        count.textContent = 'Showing ' + shown + ' project' + (shown === 1 ? '' : 's');
        empty.hidden = shown !== 0;
    }

    function choose(attr, value) {
        root.querySelectorAll('[' + attr + ']').forEach(function (b) {
            var on = b.getAttribute(attr) === value;
            b.classList.toggle('is-active', on);
            b.setAttribute('aria-pressed', on);
        });
    }

    search.addEventListener('input', function () {
        state.q = search.value.trim().toLowerCase();
        apply();
    });

    root.addEventListener('click', function (e) {
        var cat = e.target.closest('[data-tp-category]');
        var st = e.target.closest('[data-tp-status]');
        if (cat) {
            state.category = cat.getAttribute('data-tp-category');
            choose('data-tp-category', state.category);
            apply();
        }
        if (st) {
            state.status = st.getAttribute('data-tp-status');
            choose('data-tp-status', state.status);
            apply();
        }
        if (e.target.closest('[data-tp-reset]')) {
            state = { q: '', category: 'all', status: 'all' };
            search.value = '';
            choose('data-tp-category', 'all');
            choose('data-tp-status', 'all');
            apply();
        }
    });
})();

// group digits with commas as the user types (Number to Words input)
document.querySelectorAll('[data-group-digits]').forEach(function (input) {
    input.addEventListener('input', function () {
        var digits = input.value.replace(/\D/g, '');
        input.value = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    });
});
