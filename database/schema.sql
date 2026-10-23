--
-- PostgreSQL database dump
--

\restrict KBKnbR8bhgjnkhmoGYIDaYsoZcZdx4JidR3CfkEWEhJYLuOKbjCIakfrPPFHwuA

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

-- Started on 2026-10-22 17:20:42

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 236 (class 1255 OID 16579)
-- Name: proteger_datos_originales_atencion(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.proteger_datos_originales_atencion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.fecha_hora IS DISTINCT FROM OLD.fecha_hora THEN
        RAISE EXCEPTION
            'No se puede cambiar la fecha original de la atención.';
    END IF;

    IF NEW.usuario_id IS DISTINCT FROM OLD.usuario_id THEN
        RAISE EXCEPTION
            'No se puede cambiar el usuario que registró la atención.';
    END IF;

    IF NEW IS DISTINCT FROM OLD THEN
        NEW.fecha_modificacion := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.proteger_datos_originales_atencion() OWNER TO postgres;

--
-- TOC entry 237 (class 1255 OID 16604)
-- Name: registrar_modificacion_estudiante(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.registrar_modificacion_estudiante() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fecha_modificacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.registrar_modificacion_estudiante() OWNER TO postgres;

--
-- TOC entry 235 (class 1255 OID 16577)
-- Name: validar_descripcion_diagnostico(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.validar_descripcion_diagnostico() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_diagnostico VARCHAR(100);
BEGIN
    SELECT nombre
    INTO v_diagnostico
    FROM diagnostico
    WHERE id = NEW.diagnostico_id;

    IF v_diagnostico = 'Otros'
       AND NULLIF(TRIM(NEW.descripcion_diagnostico), '') IS NULL THEN
        RAISE EXCEPTION
            'Debe ingresar una descripción cuando el diagnóstico es Otros.';
    END IF;

    IF v_diagnostico <> 'Otros'
       AND NEW.descripcion_diagnostico IS NOT NULL THEN
        RAISE EXCEPTION
            'La descripción adicional solo se permite para el diagnóstico Otros.';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.validar_descripcion_diagnostico() OWNER TO postgres;

--
-- TOC entry 234 (class 1255 OID 16575)
-- Name: validar_estudiante_academico(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.validar_estudiante_academico() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_nivel VARCHAR(20);
BEGIN
    SELECT nivel
    INTO v_nivel
    FROM curso
    WHERE id = NEW.curso_id;

    IF v_nivel IN ('Inicial', 'EGB') THEN
        IF NEW.paralelo_id IS NULL
           OR NEW.especialidad_id IS NOT NULL THEN
            RAISE EXCEPTION
                'Inicial y EGB requieren paralelo y no permiten especialidad.';
        END IF;

    ELSIF v_nivel = 'Bachillerato' THEN
        IF NEW.especialidad_id IS NULL
           OR NEW.paralelo_id IS NOT NULL THEN
            RAISE EXCEPTION
                'Bachillerato requiere especialidad y no permite paralelo.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.validar_estudiante_academico() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 232 (class 1259 OID 16534)
-- Name: atencion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.atencion (
    id bigint NOT NULL,
    estudiante_id bigint NOT NULL,
    fecha_hora timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    saturacion numeric,
    frecuencia_cardiaca numeric,
    temperatura numeric,
    diagnostico_id bigint NOT NULL,
    descripcion_diagnostico text,
    recomendacion text,
    usuario_id bigint NOT NULL,
    modificado_por bigint,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE public.atencion OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16533)
-- Name: atencion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.atencion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.atencion_id_seq OWNER TO postgres;

--
-- TOC entry 5109 (class 0 OID 0)
-- Dependencies: 231
-- Name: atencion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.atencion_id_seq OWNED BY public.atencion.id;


--
-- TOC entry 220 (class 1259 OID 16442)
-- Name: curso; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.curso (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    nivel character varying(20) NOT NULL,
    CONSTRAINT chk_curso_nivel CHECK (((nivel)::text = ANY ((ARRAY['Inicial'::character varying, 'EGB'::character varying, 'Bachillerato'::character varying])::text[])))
);


ALTER TABLE public.curso OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16441)
-- Name: curso_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.curso_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.curso_id_seq OWNER TO postgres;

--
-- TOC entry 5110 (class 0 OID 0)
-- Dependencies: 219
-- Name: curso_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.curso_id_seq OWNED BY public.curso.id;


--
-- TOC entry 226 (class 1259 OID 16477)
-- Name: diagnostico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.diagnostico (
    id bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.diagnostico OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16476)
-- Name: diagnostico_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.diagnostico_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.diagnostico_id_seq OWNER TO postgres;

--
-- TOC entry 5111 (class 0 OID 0)
-- Dependencies: 225
-- Name: diagnostico_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.diagnostico_id_seq OWNED BY public.diagnostico.id;


--
-- TOC entry 224 (class 1259 OID 16466)
-- Name: especialidad; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.especialidad (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL
);


ALTER TABLE public.especialidad OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16465)
-- Name: especialidad_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.especialidad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.especialidad_id_seq OWNER TO postgres;

--
-- TOC entry 5112 (class 0 OID 0)
-- Dependencies: 223
-- Name: especialidad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.especialidad_id_seq OWNED BY public.especialidad.id;


--
-- TOC entry 230 (class 1259 OID 16506)
-- Name: estudiante; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estudiante (
    id bigint NOT NULL,
    nombre character varying(150) NOT NULL,
    curso_id bigint NOT NULL,
    paralelo_id bigint,
    especialidad_id bigint,
    sexo character varying(20) NOT NULL,
    modificado_por bigint,
    fecha_modificacion timestamp without time zone,
    CONSTRAINT chk_estudiante_paralelo_especialidad CHECK ((NOT ((paralelo_id IS NOT NULL) AND (especialidad_id IS NOT NULL)))),
    CONSTRAINT chk_estudiante_sexo CHECK (((sexo)::text = ANY ((ARRAY['Masculino'::character varying, 'Femenino'::character varying])::text[])))
);


ALTER TABLE public.estudiante OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16505)
-- Name: estudiante_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.estudiante_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.estudiante_id_seq OWNER TO postgres;

--
-- TOC entry 5113 (class 0 OID 0)
-- Dependencies: 229
-- Name: estudiante_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.estudiante_id_seq OWNED BY public.estudiante.id;


--
-- TOC entry 222 (class 1259 OID 16455)
-- Name: paralelo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.paralelo (
    id bigint NOT NULL,
    nombre character varying(10) NOT NULL
);


ALTER TABLE public.paralelo OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16454)
-- Name: paralelo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.paralelo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.paralelo_id_seq OWNER TO postgres;

--
-- TOC entry 5114 (class 0 OID 0)
-- Dependencies: 221
-- Name: paralelo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.paralelo_id_seq OWNED BY public.paralelo.id;


--
-- TOC entry 228 (class 1259 OID 16490)
-- Name: usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario (
    id bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    rol character varying(20) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    auth_user_id uuid,
    CONSTRAINT chk_usuario_rol CHECK (((rol)::text = ANY ((ARRAY['Usuario'::character varying, 'Admin'::character varying])::text[])))
);


ALTER TABLE public.usuario OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16583)
-- Name: usuario_credencial; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario_credencial (
    usuario_id bigint NOT NULL,
    password_hash text NOT NULL,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.usuario_credencial OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16489)
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_seq OWNER TO postgres;

--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 227
-- Name: usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;


--
-- TOC entry 4902 (class 2604 OID 16537)
-- Name: atencion id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion ALTER COLUMN id SET DEFAULT nextval('public.atencion_id_seq'::regclass);


--
-- TOC entry 4894 (class 2604 OID 16445)
-- Name: curso id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curso ALTER COLUMN id SET DEFAULT nextval('public.curso_id_seq'::regclass);


--
-- TOC entry 4897 (class 2604 OID 16480)
-- Name: diagnostico id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnostico ALTER COLUMN id SET DEFAULT nextval('public.diagnostico_id_seq'::regclass);


--
-- TOC entry 4896 (class 2604 OID 16469)
-- Name: especialidad id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.especialidad ALTER COLUMN id SET DEFAULT nextval('public.especialidad_id_seq'::regclass);


--
-- TOC entry 4901 (class 2604 OID 16509)
-- Name: estudiante id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante ALTER COLUMN id SET DEFAULT nextval('public.estudiante_id_seq'::regclass);


--
-- TOC entry 4895 (class 2604 OID 16458)
-- Name: paralelo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paralelo ALTER COLUMN id SET DEFAULT nextval('public.paralelo_id_seq'::regclass);


--
-- TOC entry 4899 (class 2604 OID 16493)
-- Name: usuario id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);


--
-- TOC entry 4937 (class 2606 OID 16547)
-- Name: atencion atencion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion
    ADD CONSTRAINT atencion_pkey PRIMARY KEY (id);


--
-- TOC entry 4910 (class 2606 OID 16451)
-- Name: curso curso_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curso
    ADD CONSTRAINT curso_pkey PRIMARY KEY (id);


--
-- TOC entry 4922 (class 2606 OID 16486)
-- Name: diagnostico diagnostico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnostico
    ADD CONSTRAINT diagnostico_pkey PRIMARY KEY (id);


--
-- TOC entry 4918 (class 2606 OID 16473)
-- Name: especialidad especialidad_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.especialidad
    ADD CONSTRAINT especialidad_pkey PRIMARY KEY (id);


--
-- TOC entry 4932 (class 2606 OID 16517)
-- Name: estudiante estudiante_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT estudiante_pkey PRIMARY KEY (id);


--
-- TOC entry 4914 (class 2606 OID 16462)
-- Name: paralelo paralelo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paralelo
    ADD CONSTRAINT paralelo_pkey PRIMARY KEY (id);


--
-- TOC entry 4912 (class 2606 OID 16453)
-- Name: curso uq_curso_nombre; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curso
    ADD CONSTRAINT uq_curso_nombre UNIQUE (nombre);


--
-- TOC entry 4924 (class 2606 OID 16488)
-- Name: diagnostico uq_diagnostico_nombre; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnostico
    ADD CONSTRAINT uq_diagnostico_nombre UNIQUE (nombre);


--
-- TOC entry 4920 (class 2606 OID 16475)
-- Name: especialidad uq_especialidad_nombre; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.especialidad
    ADD CONSTRAINT uq_especialidad_nombre UNIQUE (nombre);


--
-- TOC entry 4916 (class 2606 OID 16464)
-- Name: paralelo uq_paralelo_nombre; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paralelo
    ADD CONSTRAINT uq_paralelo_nombre UNIQUE (nombre);


--
-- TOC entry 4926 (class 2606 OID 16504)
-- Name: usuario uq_usuario_email; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT uq_usuario_email UNIQUE (email);


--
-- TOC entry 4928 (class 2606 OID 16582)
-- Name: usuario usuario_auth_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_auth_user_id_key UNIQUE (auth_user_id);


--
-- TOC entry 4943 (class 2606 OID 16593)
-- Name: usuario_credencial usuario_credencial_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario_credencial
    ADD CONSTRAINT usuario_credencial_pkey PRIMARY KEY (usuario_id);


--
-- TOC entry 4930 (class 2606 OID 16502)
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- TOC entry 4938 (class 1259 OID 16572)
-- Name: idx_atencion_diagnostico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_atencion_diagnostico ON public.atencion USING btree (diagnostico_id);


--
-- TOC entry 4939 (class 1259 OID 16571)
-- Name: idx_atencion_estudiante; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_atencion_estudiante ON public.atencion USING btree (estudiante_id);


--
-- TOC entry 4940 (class 1259 OID 16574)
-- Name: idx_atencion_fecha_hora; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_atencion_fecha_hora ON public.atencion USING btree (fecha_hora);


--
-- TOC entry 4941 (class 1259 OID 16573)
-- Name: idx_atencion_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_atencion_usuario ON public.atencion USING btree (usuario_id);


--
-- TOC entry 4933 (class 1259 OID 16568)
-- Name: idx_estudiante_curso; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_estudiante_curso ON public.estudiante USING btree (curso_id);


--
-- TOC entry 4934 (class 1259 OID 16570)
-- Name: idx_estudiante_especialidad; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_estudiante_especialidad ON public.estudiante USING btree (especialidad_id);


--
-- TOC entry 4935 (class 1259 OID 16569)
-- Name: idx_estudiante_paralelo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_estudiante_paralelo ON public.estudiante USING btree (paralelo_id);


--
-- TOC entry 4955 (class 2620 OID 16580)
-- Name: atencion trg_proteger_datos_originales_atencion; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_proteger_datos_originales_atencion BEFORE UPDATE ON public.atencion FOR EACH ROW EXECUTE FUNCTION public.proteger_datos_originales_atencion();


--
-- TOC entry 4953 (class 2620 OID 16605)
-- Name: estudiante trg_registrar_modificacion_estudiante; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_registrar_modificacion_estudiante BEFORE UPDATE ON public.estudiante FOR EACH ROW EXECUTE FUNCTION public.registrar_modificacion_estudiante();


--
-- TOC entry 4956 (class 2620 OID 16578)
-- Name: atencion trg_validar_descripcion_diagnostico; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_validar_descripcion_diagnostico BEFORE INSERT OR UPDATE OF diagnostico_id, descripcion_diagnostico ON public.atencion FOR EACH ROW EXECUTE FUNCTION public.validar_descripcion_diagnostico();


--
-- TOC entry 4954 (class 2620 OID 16576)
-- Name: estudiante trg_validar_estudiante_academico; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_validar_estudiante_academico BEFORE INSERT OR UPDATE OF curso_id, paralelo_id, especialidad_id ON public.estudiante FOR EACH ROW EXECUTE FUNCTION public.validar_estudiante_academico();


--
-- TOC entry 4948 (class 2606 OID 16553)
-- Name: atencion fk_atencion_diagnostico; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion
    ADD CONSTRAINT fk_atencion_diagnostico FOREIGN KEY (diagnostico_id) REFERENCES public.diagnostico(id);


--
-- TOC entry 4949 (class 2606 OID 16548)
-- Name: atencion fk_atencion_estudiante; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion
    ADD CONSTRAINT fk_atencion_estudiante FOREIGN KEY (estudiante_id) REFERENCES public.estudiante(id);


--
-- TOC entry 4950 (class 2606 OID 16563)
-- Name: atencion fk_atencion_modificado_por; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion
    ADD CONSTRAINT fk_atencion_modificado_por FOREIGN KEY (modificado_por) REFERENCES public.usuario(id);


--
-- TOC entry 4951 (class 2606 OID 16558)
-- Name: atencion fk_atencion_usuario; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.atencion
    ADD CONSTRAINT fk_atencion_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- TOC entry 4944 (class 2606 OID 16518)
-- Name: estudiante fk_estudiante_curso; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT fk_estudiante_curso FOREIGN KEY (curso_id) REFERENCES public.curso(id);


--
-- TOC entry 4945 (class 2606 OID 16528)
-- Name: estudiante fk_estudiante_especialidad; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT fk_estudiante_especialidad FOREIGN KEY (especialidad_id) REFERENCES public.especialidad(id);


--
-- TOC entry 4946 (class 2606 OID 16599)
-- Name: estudiante fk_estudiante_modificado_por; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT fk_estudiante_modificado_por FOREIGN KEY (modificado_por) REFERENCES public.usuario(id) ON DELETE SET NULL;


--
-- TOC entry 4947 (class 2606 OID 16523)
-- Name: estudiante fk_estudiante_paralelo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudiante
    ADD CONSTRAINT fk_estudiante_paralelo FOREIGN KEY (paralelo_id) REFERENCES public.paralelo(id);


--
-- TOC entry 4952 (class 2606 OID 16594)
-- Name: usuario_credencial usuario_credencial_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario_credencial
    ADD CONSTRAINT usuario_credencial_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;


-- Completed on 2026-10-22 17:20:42

--
-- PostgreSQL database dump complete
--

\unrestrict KBKnbR8bhgjnkhmoGYIDaYsoZcZdx4JidR3CfkEWEhJYLuOKbjCIakfrPPFHwuA

